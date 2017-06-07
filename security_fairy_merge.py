def lambda_handler(event, context):

    merged_payload = {}

    for item in event:
        if item is not None and item is not "":
           merged_payload.update(item)

    return merged_payload
