package uk.co.crwilliams.opensource.MyHomeApp;

import android.content.*;
import android.widget.ListView;
import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.services.sqs.AmazonSQSClient;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.TextView;
import uk.co.crwilliams.opensource.MyHomeApp.controller.Adapter;
import uk.co.crwilliams.opensource.MyHomeApp.database.DataRow;
import uk.co.crwilliams.opensource.MyHomeApp.database.Database;

import java.util.ArrayList;

/**
 * Main UI for the demo app.
 */
public class MyHomeAppActivity extends com.google.android.gcm.demo.app.DemoActivity {

    private AmazonSQSClient sqsClient;

    private Database database;
    private Adapter adapter;
    private ArrayList<DataRow> rows;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.main);

        database = new Database(getApplicationContext());

        registerReceiver(mHandleMessageReceiver,
                new IntentFilter("uk.co.crwilliams.opensource.home.UPDATE"));

        AWSCredentials credentials = new BasicAWSCredentials(Constants.AWS_ACCESS_KEY, Constants.AWS_SECRET_KEY);
        this.sqsClient = new AmazonSQSClient(credentials);
        this.sqsClient.setEndpoint(Constants.AWS_SQS_ENDPOINT);

        rows = new ArrayList<DataRow>();
        database.updateData(rows);

        adapter = new Adapter(this, rows);
        ((ListView)this.findViewById(R.id.listView)).setAdapter(adapter);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();

        unregisterReceiver(mHandleMessageReceiver);

        if (database != null) {
            database.close();
        }
    }

    private void queue(String string) {
        QueueMessageTaskParams params = new QueueMessageTaskParams(sqsClient, string);
        new QueueMessageTask().execute(params);
    }

    public void button(View v) {
        Log.i(Constants.TAG, v.toString());
        String room = ((TextView)((View)v.getParent()).findViewById(R.id.text_room_name)).getText().toString();

        switch(v.getId())
        {
            case R.id.button_on:
                queue(room + "/on");
                break;
            case R.id.button_off:
                queue(room + "/off");
                break;
            case R.id.button_low:
                queue(room + "/" + Constants.LEVEL_LOW);
                break;
            case R.id.button_medium:
                queue(room + "/" + Constants.LEVEL_MEDIUM);
                break;
            case R.id.button_high:
                queue(room + "/" + Constants.LEVEL_HIGH);
                break;
        }
    }

    private final BroadcastReceiver mHandleMessageReceiver =
            new BroadcastReceiver() {
                @Override
                public void onReceive(Context context, Intent intent) {
                    Log.i(Constants.TAG, "MyHomeAppActivity.onReceive() intent :" + intent);

                    database.updateData(rows);
                    adapter.notifyDataSetChanged();
                }
            };
}
