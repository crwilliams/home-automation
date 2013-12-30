package uk.co.crwilliams.opensource.MyHomeApp;

import android.os.AsyncTask;
import com.amazonaws.services.sqs.model.GetQueueUrlRequest;
import com.amazonaws.services.sqs.model.SendMessageRequest;

import java.net.UnknownHostException;

class QueueMessageTask extends AsyncTask<QueueMessageTaskParams, Void, Void> {

    protected Void doInBackground(QueueMessageTaskParams... params) {
        try {
            String url = params[0].getSqsClient().getQueueUrl(
                    new GetQueueUrlRequest().withQueueName(Constants.AWS_SQS_QUEUE_NAME)).getQueueUrl();
            params[0].getSqsClient().sendMessage(
                    new SendMessageRequest().withQueueUrl(url).withMessageBody(params[0].getMessage()));
        } catch (Exception ex) {

        }
        return null;
    }
}
