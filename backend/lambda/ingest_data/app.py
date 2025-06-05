# lambda/ingest_data/app.py
import csv
import io
import json
import logging
import os
from decimal import Decimal

import boto3

# Import shared utilities
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.error_handler import handle_error, ValidationError
from utils.response_formatter import format_success_response
from utils.logging_utils import log_event, log_lambda_execution

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize clients
dynamodb_client = boto3.resource("dynamodb")
s3_client = boto3.client("s3")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)


def check_if_processed(bucket, key):
    """Check if file was already processed by looking at metadata."""
    try:
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = response.get("Metadata", {})
        return metadata.get("processed") == "true"
    except Exception as e:
        logger.error(f"Error checking metadata: {str(e)}")
        return False


def mark_file_as_processed(bucket, key):
    """Mark file as processed by setting metadata."""
    copy_source = {"Bucket": bucket, "Key": key}
    s3_client.copy_object(
        CopySource=copy_source,
        Bucket=bucket,
        Key=key,
        Metadata={"processed": "true"},
        MetadataDirective="REPLACE",
    )


@log_lambda_execution
def lambda_handler(event, context):
    # Log the incoming event
    log_event(event, context)

    try:
        # Get the S3 bucket and key from the event
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = event["Records"][0]["s3"]["object"]["key"]

        # Check if file was already processed
        if check_if_processed(bucket, key):
            logger.info(f"File {key} was already processed. Skipping.")
            return format_success_response(
                {
                    "message": f"File {key} was already processed. Skipping.",
                    "status": "skipped",
                }
            )

        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response["Body"].read().decode("utf-8")

        # Process CSV data
        csv_reader = csv.DictReader(io.StringIO(file_content))

        # Track processing statistics
        processed_count = 0
        error_count = 0

        # Validate CSV structure
        required_fields = [
            "payer_account_id",
            "invoice_id",
            "product_code",
            "bill_period_start_date",
        ]
        sample_row = next(csv_reader, None)
        if not sample_row:
            raise ValidationError("CSV file is empty or improperly formatted")

        for field in required_fields:
            if field not in sample_row:
                raise ValidationError(f"CSV file is missing required field: {field}")

        # Reset the reader to include the first row
        csv_reader = csv.DictReader(io.StringIO(file_content))

        # Batch write to DynamoDB
        with table.batch_writer() as batch:
            for row_num, row in enumerate(
                csv_reader, start=2
            ):  # Start at 2 to account for header row
                try:
                    # Clean and format the data
                    item = {
                        "payer_account_id": str(row["payer_account_id"]).strip(),
                        "invoice_id#product_code": f"{row['invoice_id']}#{row['product_code']}",
                        "bill_period_start_date": row["bill_period_start_date"],
                        "invoice_id": row["invoice_id"],
                        "product_code": row["product_code"],
                        "cost_before_tax": Decimal(str(row["cost_before_tax"]))
                        if row["cost_before_tax"]
                        else Decimal("0"),
                    }

                    # Add optional fields if they exist and have values
                    for field in [
                        "credits_before_discount",
                        "credits_after_discount",
                        "sp_discount",
                        "ubd_discount",
                        "prc_discount",
                        "rvd_discount",
                        "edp_discount",
                        "edp_discount_%",
                    ]:
                        if field in row and row[field]:
                            try:
                                # Convert to Decimal instead of float
                                item[field.replace("%", "percent")] = Decimal(
                                    str(row[field])
                                )
                            except:
                                item[field.replace("%", "percent")] = Decimal("0")

                    # Write to DynamoDB
                    batch.put_item(Item=item)
                    processed_count += 1

                except Exception as row_error:
                    logger.error(
                        f"Row {row_num}: Error processing row: {str(row_error)}"
                    )
                    error_count += 1

        # Mark file as processed
        mark_file_as_processed(bucket, key)
        logger.info(f"Successfully processed and marked file {key}")

        return format_success_response(
            {
                "message": f"Successfully processed {key}",
                "statistics": {
                    "processed": processed_count,
                    "errors": error_count,
                    "total": processed_count + error_count,
                },
            }
        )

    except ValidationError as e:
        # Handle validation errors
        return handle_error(
            e,
            {
                "aws_request_id": context.aws_request_id,
                "bucket": bucket if "bucket" in locals() else None,
                "key": key if "key" in locals() else None,
            },
        )
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return handle_error(
            e,
            {
                "aws_request_id": context.aws_request_id,
                "bucket": bucket if "bucket" in locals() else None,
                "key": key if "key" in locals() else None,
                "function_name": context.function_name,
            },
        )
