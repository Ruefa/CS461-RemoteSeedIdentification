package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.Toast;

import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

import java.util.ArrayList;
import java.util.Arrays;

public class ResultsController extends AppCompatActivity implements ResultsListRVAdapter.OnResultsClickListener {
    private static final String TAG = "ResultsController";

    private static final String ERROR_REPORT = "ERROR: Unable to receive report from server.";
    private static final String ERROR_UNKNOWN = "ERROR: Unable to connect to server.";

    private ResultsListRVAdapter mResultsRVAdapter;
    private ProgressBar mpbResultsRV;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        mpbResultsRV = findViewById(R.id.pb_results_rv);
        mpbResultsRV.setVisibility(View.VISIBLE);

        mBroadcastManager = LocalBroadcastManager.getInstance(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(BROADCAST_ACTION);
        mBroadcastManager.registerReceiver(mBroadcastReceiver, intentFilter);

        Intent listIntent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, "request list");
        bundle.putString(SocketService.ACTION_KEY, ACTION_VIEW_RESULTS);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        listIntent.putExtras(bundle);
        startService(listIntent);

        getSupportActionBar().setTitle(getString(R.string.results_actionbar_title));

        initResultsList();
    }

    private ArrayList<Bitmap> testBitmaps(){
        ArrayList<Bitmap> bitmaps = new ArrayList<>();

        Bitmap singleBitmap = BitmapFactory.decodeResource(getResources(),
                R.drawable.results_example);

        for(int i=0; i<10; i++) {
            bitmaps.add(singleBitmap);
        }

        return bitmaps;
    }

    private void initResultsList(){
        RecyclerView rvResults = findViewById(R.id.rv_results_list);
        mResultsRVAdapter = new ResultsListRVAdapter(this);
        rvResults.setAdapter(mResultsRVAdapter);
        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setReverseLayout(true);
        layoutManager.setStackFromEnd(true);
        rvResults.setLayoutManager(layoutManager);
        rvResults.setHasFixedSize(true);

        // create list of tests strings
        ArrayList<String> testList = new ArrayList<>();
        for(int i=1; i<=10; i++) {
            testList.add("9/" + String.valueOf(i) + "/2018 13:05");
        }
        testList = new ArrayList<>();
        testList.add(getString(R.string.loading_results));
        //mResultsRVAdapter.updateItems(testList, testBitmaps());
    }

    public final static String BROADCAST_ACTION = "results";
    public final static String ACTION_VIEW_RESULTS = "view_results";
    public final static String ACTION_REQUEST_RESULT = "request_result";
    private LocalBroadcastManager mBroadcastManager;
    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            mpbResultsRV.setVisibility(View.INVISIBLE);

            if(intent.getStringExtra(SocketService.ACTION_KEY) != null) {
                if (intent.getStringExtra(SocketService.ACTION_KEY).equals(ACTION_VIEW_RESULTS)) {
                    String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
                    Log.d(TAG, results);

                    // split results over | delimiter
                    String[] resultArray = results.split("\\|");
                    if(resultArray.length > 1) {
                        ArrayList<String> resultList = new ArrayList<String>(Arrays.asList(resultArray));
                        // first result is error code. remove it to get only data
                        resultList.remove(0);
                        Log.d(TAG, "resultList size: " + resultList.size());
                        Log.d(TAG, "result: " + resultList.get(0));
                        if (resultList.size() > 0 && !resultList.get(0).equals("")) {
                            mResultsRVAdapter.updateItems(resultList, testBitmaps());
                        } else {
                            ArrayList<String> emptyList = new ArrayList<>();
                            emptyList.add("No results to display");
                            mResultsRVAdapter.updateItems(emptyList, testBitmaps());
                        }
                    }
                } else if (intent.getStringExtra(SocketService.ACTION_KEY).equals(ACTION_REQUEST_RESULT)) {
                    Log.d(TAG, "result request received");
                    String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
                    if(results != ServerUtils.FAILURE) {
                        Intent resultDetailIntent = new Intent(context, ResultDetailController.class);
                        resultDetailIntent.putExtra(SocketService.BROADCAST_KEY, results);
                        startActivity(resultDetailIntent);
                    } else{
                        errorToast(ERROR_REPORT);
                    }
                }
            } else {
                errorToast(ERROR_UNKNOWN);
            }
        }
    };

    @Override
    public void onResultsClick(String item) {
        Log.d(TAG, "item clicked: " + item);

        mpbResultsRV.setVisibility(View.VISIBLE);

        Intent intent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, item);
        bundle.putString(SocketService.ACTION_KEY, ACTION_REQUEST_RESULT);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        intent.putExtras(bundle);
        startService(intent);
    }

    private void goResultDetail(){
        Intent intent = new Intent(this, ResultDetailController.class);
        startActivity(intent);
    }

    private void errorToast(String errorText){
        Toast.makeText(getApplicationContext(), errorText, Toast.LENGTH_LONG).show();
    }
}
