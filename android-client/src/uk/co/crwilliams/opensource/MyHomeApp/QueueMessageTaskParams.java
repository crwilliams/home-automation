package uk.co.crwilliams.opensource.MyHomeApp;

import com.amazonaws.services.sqs.AmazonSQSClient;

class QueueMessageTaskParams {
    private final AmazonSQSClient sqsClient;
    private final String message;

    public QueueMessageTaskParams(AmazonSQSClient sqsClient, String message) {
        this.sqsClient = sqsClient;
        this.message = message;
    }

    public AmazonSQSClient getSqsClient() {
        return sqsClient;
    }

    public String getMessage() {
        return message;
    }
}
