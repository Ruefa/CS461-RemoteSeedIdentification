package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;

public class ResultsController extends AppCompatActivity {
    private static final String TAG = "ResultsController";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        Intent listIntent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, ACTION_VIEW_RESULTS);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        listIntent.putExtras(bundle);
        startService(listIntent);
    }

    public final static String BROADCAST_ACTION = "results";
    public final static String ACTION_VIEW_RESULTS = "view_results";
    private LocalBroadcastManager mBroadcastManager;
    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Log.d(TAG, "receiving");
        }
    };
}
