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

import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

import java.util.ArrayList;
import java.util.Arrays;

public class ResultsController extends AppCompatActivity implements ResultsListRVAdapter.OnResultsClickListener {
    private static final String TAG = "ResultsController";

    private ResultsListRVAdapter mResultsRVAdapter;
    private ProgressBar mpbResultsRV;
    private ImageView mResultView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_results);

        mResultView = findViewById(R.id.iv_result);

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
        mResultsRVAdapter.updateItems(testList, testBitmaps());
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

                    String[] resultArray = results.split("\\|");
                    ArrayList<String> resultList = new ArrayList<String>(Arrays.asList(resultArray));
                    Log.d(TAG, "resultList size: " + resultList.size());
                    Log.d(TAG, "result: " + resultList.get(0));
                    if (resultList.size() > 0 && !resultList.get(0).equals("")) {
                        mResultsRVAdapter.updateItems(resultList, testBitmaps());
                    } else {
                        ArrayList<String> emptyList = new ArrayList<>();
                        emptyList.add("No results to display");
                        mResultsRVAdapter.updateItems(emptyList, testBitmaps());
                    }
                } else if (intent.getStringExtra(SocketService.ACTION_KEY).equals(ACTION_REQUEST_RESULT)) {
                    Log.d(TAG, "result request received");
                    String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
                    Log.d(TAG, intent.getStringExtra(SocketService.BROADCAST_KEY));

                    String[] resultArray = results.split("\n");
                    Log.d(TAG, Arrays.toString(resultArray));

                    float prg = Float.valueOf(resultArray[0].split(":")[1]) * 100;
                    float tf = Float.valueOf(resultArray[1].split(":")[1]) * 100;

                    byte[] imageBytes = MainActivity.fileToBytes(resultArray[2]);
                    Bitmap thumbBitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
                    mResultView.setImageBitmap(thumbBitmap);

                    BarGraphSeries<DataPoint> series = new BarGraphSeries<>(new DataPoint[]{
                            new DataPoint(0, prg),
                            new DataPoint(2, tf)
                    });
                    //mGraphView.removeAllSeries();
                    //mGraphView.addSeries(series);

                    series.setValueDependentColor(new ValueDependentColor<DataPoint>() {
                        @Override
                        public int get(DataPoint data) {
                            return Color.rgb((int) data.getX() * 255 / 4, (int) Math.abs(data.getY() * 255 / 6), 100);
                        }
                    });
                    series.setSpacing(50);

                    series.setDrawValuesOnTop(true);
                    series.setValuesOnTopColor(Color.RED);
                }
            } else {
                //display error
            }
        }
    };

    @Override
    public void onResultsClick(String item) {
        Log.d(TAG, "item clicked: " + item);
        Intent intent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, item);
        bundle.putString(SocketService.ACTION_KEY, ACTION_REQUEST_RESULT);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        intent.putExtras(bundle);
        startService(intent);

        goResultDetail();
    }

    private void goResultDetail(){
        Intent intent = new Intent(this, ResultDetailController.class);
        startActivity(intent);
    }
}
