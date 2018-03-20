package com.capstone.remoteseedidentification;

import android.app.IntentService;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;

import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

import java.util.ArrayList;

public class ResultsController extends AppCompatActivity implements ResultsListRVAdapter.OnResultsClickListener {
    private static final String TAG = "ResultsController";

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
        bundle.putString(SocketService.SEND_MESSAGE_KEY, ACTION_VIEW_RESULTS);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        listIntent.putExtras(bundle);
        startService(listIntent);

        initResultsList();

        initResultsGraph();
    }

    private void initResultsList(){
        RecyclerView rvResults = findViewById(R.id.rv_results_list);
        mResultsRVAdapter = new ResultsListRVAdapter(this);
        rvResults.setAdapter(mResultsRVAdapter);
        rvResults.setLayoutManager(new LinearLayoutManager(this));
        rvResults.setHasFixedSize(true);

        ArrayList<String> testList = new ArrayList<>();
        for(int i=1; i<=10; i++) {
            testList.add("results " + String.valueOf(i));
        }
        mResultsRVAdapter.updateItems(testList);
    }
    
    private void initResultsGraph(){

        GraphView graphView = findViewById(R.id.graph_results);
        BarGraphSeries<DataPoint> series = new BarGraphSeries<>(new DataPoint[] {
                new DataPoint(0, 15),
                new DataPoint(1, 20),
                new DataPoint(2, 45),
                new DataPoint(3, 10),
                new DataPoint(4, 10)
        });
        graphView.addSeries(series);

        //styling
        series.setValueDependentColor(new ValueDependentColor<DataPoint>() {
            @Override
            public int get(DataPoint data) {
                return Color.rgb((int) data.getX()*255/4, (int) Math.abs(data.getY()*255/6), 100);
            }
        });
        series.setSpacing(50);

        series.setDrawValuesOnTop(true);
        series.setValuesOnTopColor(Color.RED);
        graphView.getViewport().setYAxisBoundsManual(true);
        graphView.getViewport().setMaxY(100);
    }

    public final static String BROADCAST_ACTION = "results";
    public final static String ACTION_VIEW_RESULTS = "view_results";
    public final static String ACTION_REQUEST_RESULT = "request_result";
    private LocalBroadcastManager mBroadcastManager;
    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
            Log.d(TAG, results);

            mpbResultsRV.setVisibility(View.INVISIBLE);
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
    }
}
