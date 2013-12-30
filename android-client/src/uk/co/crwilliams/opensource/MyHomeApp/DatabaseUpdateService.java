package uk.co.crwilliams.opensource.MyHomeApp;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import uk.co.crwilliams.opensource.MyHomeApp.database.Database;

public class DatabaseUpdateService extends com.google.android.gcm.demo.app.GcmIntentService {

    private Database doh;

    @Override
    public void onCreate() {
        super.onCreate();
        Log.i(Constants.TAG, "Create DatabaseUpdateService");
        doh = new Database(getApplicationContext());
        Log.i(Constants.TAG, "Done creating DatabaseUpdateService");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (doh != null) {
            doh.close();
        }
    }

    @Override
    protected void processUpdate(Bundle extras) {
        processUpdate(
                extras.getString("room"),
                extras.getString("value"),
                extras.getString("type"),
                Integer.parseInt(extras.getString("time")));
    }

    private void processUpdate(String room, String value, String type, int time) {
        doh.update(room, value, type, time);

        Intent intent = new Intent("uk.co.crwilliams.opensource.home.UPDATE");
        Log.i(Constants.TAG, "DatabaseUpdateService.processUpdate() time :" + time);
        getApplicationContext().sendBroadcast(intent);
    }
}
