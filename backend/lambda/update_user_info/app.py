import json
import logging
import os
import csv
import boto3
from urllib.parse import unquote_plus

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Initialize DynamoDB client
dynamodb_client = boto3.resource("dynamodb")
table_name = os.environ.get("TABLE_NAME")
table = dynamodb_client.Table(table_name)

# Initialize S3 client
s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Lambda function that processes CSV files uploaded to S3 and updates DynamoDB.

    This function:
    1. Downloads a CSV file from S3 when it's uploaded
    2. Parses the CSV file which should contain email and payer_account_id columns
    3. For each row, updates the DynamoDB table with the email and associated account IDs
    4. One email can be associated with multiple payer_account_ids (semicolon-separated)
    5. Each new file upload will overwrite existing entries with the same email

    Args:
        event (dict): S3 event notification
        context (object): Lambda context object

    Returns:
        dict: Response indicating success or failure with processing statistics
    """
    try:
        # Get bucket and key from the S3 event
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
        key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])

        logger.info(f"Processing file {key} from bucket {bucket}")

        # Download the file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = (
            response["Body"].read().decode("utf-8-sig").splitlines()
        )  # utf-8-sig handles BOM character

        # Parse CSV
        csv_reader = csv.DictReader(file_content)

        # Track processing statistics
        processed_count = 0
        skipped_count = 0
        error_count = 0

        # Process each row and update DynamoDB
        for row_num, row in enumerate(
            csv_reader, start=2
        ):  # Start at 2 to account for header row
            try:
                # Clean up field names to handle potential BOM character
                clean_row = {}
                for k, v in row.items():
                    clean_key = k.strip().replace(
                        "\ufeff", ""
                    )  # Remove BOM character if present
                    clean_row[clean_key] = v

                # Check if required fields exist
                if "email" not in clean_row or "payer_account_id" not in clean_row:
                    logger.warning(
                        f"Row {row_num}: Missing required fields after cleaning: {clean_row}"
                    )
                    skipped_count += 1
                    continue

                email = clean_row["email"].strip()
                payer_account_ids_str = clean_row["payer_account_id"].strip()

                if not email or not payer_account_ids_str:
                    logger.warning(
                        f"Row {row_num}: Skipping row with empty values: {clean_row}"
                    )
                    skipped_count += 1
                    continue

                # Validate email format (basic check)
                if "@" not in email:
                    logger.warning(f"Row {row_num}: Invalid email format: {email}")
                    skipped_count += 1
                    continue

                # Split semicolon-separated payer_account_ids
                payer_account_ids = [
                    id.strip() for id in payer_account_ids_str.split(";")
                ]

                # Update DynamoDB - store as a list of account IDs
                table.put_item(
                    Item={
                        "email": email,
                        "payer_account_ids": payer_account_ids,
                        # Add any additional fields from the CSV if needed
                    }
                )
                logger.info(
                    f"Row {row_num}: Updated user info for email: {email} with account IDs: {payer_account_ids}"
                )
                processed_count += 1

            except Exception as row_error:
                logger.error(f"Row {row_num}: Error processing row: {str(row_error)}")
                error_count += 1

        # Return success response with processing statistics
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully processed file {key}",
                    "statistics": {
                        "processed": processed_count,
                        "skipped": skipped_count,
                        "errors": error_count,
                        "total": processed_count + skipped_count + error_count,
                    },
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file: {str(e)}"),
        }
