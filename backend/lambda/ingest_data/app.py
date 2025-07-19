# lambda/ingest_data/app.py
import boto3
import pandas as pd
import io
from decimal import Decimal
import logging
import json
from botocore.exceptions import ClientError
import os
import datetime
from datetime import timezone
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb.Table(table_name)


def check_if_processed(bucket, key):
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        return response.get("Metadata", {}).get("processed") == "true"
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise


def mark_file_as_processed(bucket, key):
    copy_source = {"Bucket": bucket, "Key": key}
    s3.copy_object(
        CopySource=copy_source,
        Bucket=bucket,
        Key=key,
        Metadata={"processed": "true"},
        MetadataDirective="REPLACE",
    )


def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    upload_timestamp = datetime.datetime.now(timezone.utc).isoformat()
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    try:
        if check_if_processed(bucket, key):
            logger.info(f"File {key} has already been processed, skipping.")
            return {
                "statusCode": 200,
                "body": json.dumps(
                    {
                        "message": f"File {key} has already been processed, skipping further processing."
                    }
                ),
            }

        response = s3.get_object(Bucket=bucket, Key=key)
        excel_data = response["Body"].read()
        df = pd.read_excel(io.BytesIO(excel_data))

        required_columns = [
            "payer_account_id",
            "invoice_id",
            "product_code",
            "bill_period_start_date",
        ]
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return {
                    "statusCode": 400,
                    "body": json.dumps(
                        {
                            "message": f"Missing required column: {col}",
                            "processed": False,
                        }
                    ),
                }

        unique_items = {}
        processed_count = 0
        error_count = 0
        for index, row in df.iterrows():
            payer_account_id = str(row.get("payer_account_id", "")).strip()
            invoice_id = str(row.get("invoice_id", "")).strip()
            product_code = str(row.get("product_code", "")).strip()
            bill_period_start_date = str(row.get("bill_period_start_date", "")).strip()
            if (
                not payer_account_id
                or not invoice_id
                or not product_code
                or not bill_period_start_date
            ):
                logger.error(
                    f"Row {index}: Missing required key fields. Row data: {row}"
                )
                error_count += 1
                continue
            key_tuple = (payer_account_id, f"{invoice_id}#{product_code}")
            item = {
                "payer_account_id": payer_account_id,
                "invoice_id#product_code": key_tuple[1],
                "bill_period_start_date": bill_period_start_date,
                "invoice_id": invoice_id,
                "product_code": product_code,
            }
            # Numeric fields to check for NaN/Infinity
            numeric_fields = [
                "cost_before_tax",
                "credits_before_discount",
                "credits_after_discount",
                "sp_discount",
                "ubd_discount",
                "prc_discount",
                "rvd_discount",
                "edp_discount",
                "edp_discount_%",
            ]
            for field in numeric_fields:
                value = row.get(field)
                # Replace NaN or Infinity with 0
                if (
                    value is not None
                    and isinstance(value, float)
                    and (math.isnan(value) or math.isinf(value))
                ):
                    logger.warning(
                        f"Row {index}: Field '{field}' is NaN or Infinity, replacing with 0. Row data: {row}"
                    )
                    value = 0
                if value not in [None, ""]:
                    try:
                        item[field.replace("%", "percent")] = Decimal(str(value))
                    except Exception as e:
                        logger.error(
                            f"Row {index}: Error converting field '{field}' value '{value}' to Decimal: {e}. Row data: {row}"
                        )
                        item[field.replace("%", "percent")] = Decimal("0")
            item["upload_timestamp"] = upload_timestamp
            unique_items[key_tuple] = item

        logger.info(f"Total unique items to write: {len(unique_items)}")
        with table.batch_writer() as batch:
            for item in unique_items.values():
                logger.info(f"Writing item to DynamoDB: {item}")
                batch.put_item(Item=item)
                processed_count += 1

        logger.info(
            f"Successfully processed {processed_count} items, {error_count} errors/skipped rows."
        )

        try:
            mark_file_as_processed(bucket, key)
            logger.info(f"Successfully marked file {key} as processed")
        except Exception as e:
            logger.error(f"Error marking file as processed: {str(e)}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully processed {key}, uploaded to DynamoDB, and archived",
                    "processed": True,
                    "statistics": {
                        "processed": processed_count,
                        "errors": error_count,
                        "total": processed_count + error_count,
                    },
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": f"Error processing {key}: {str(e)}", "processed": False}
            ),
        }
