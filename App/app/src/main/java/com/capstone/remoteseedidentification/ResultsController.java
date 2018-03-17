package com.capstone.remoteseedidentification;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.Log;

import java.util.ArrayList;

public class ResultsController extends AppCompatActivity implements ResultsListRVAdapter.OnResultsClickListener {
    private static final String TAG = "ResultsController";

    private ResultsListRVAdapter mResultsRVAdapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        mBroadcastManager = LocalBroadcastManager.getInstance(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(BROADCAST_ACTION);
        mBroadcastManager.registerReceiver(mBroadcastReceiver, intentFilter);

        Intent listIntent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, ACTION_VIEW_RESULTS);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        listIntent.putExtras(bundle);
        startService(listIntent);

        initResultsList();
    }

    private void initResultsList(){
        RecyclerView rvResults = findViewById(R.id.rv_results_list);
        mResultsRVAdapter = new ResultsListRVAdapter(this);
        rvResults.setAdapter(mResultsRVAdapter);
        rvResults.setLayoutManager(new LinearLayoutManager(this));
        rvResults.setHasFixedSize(true);
    }

    public final static String BROADCAST_ACTION = "results";
    public final static String ACTION_VIEW_RESULTS = "view_results";
    private LocalBroadcastManager mBroadcastManager;
    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
            Log.d(TAG, results);

            ArrayList<String> testList = new ArrayList<>();
            for(int i=1; i<=10; i++) {
                testList.add("results " + String.valueOf(i));
            }
            mResultsRVAdapter.updateItems(testList);
        }
    };

    @Override
    public void onResultsClick(String item) {
        Log.d(TAG, "item clicked: " + item);
    }
}
