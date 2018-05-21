package com.capstone.remoteseedidentification;

import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.LinearLayoutManager;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.View;
import android.widget.ProgressBar;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.Arrays;

public class ResultsController extends AppCompatActivity
        implements ResultsListRVAdapter.OnResultsClickListener, ResultsListRVAdapter.OnDeleteClickListener {
    private static final String TAG = "ResultsController";

    private static final String ERROR_REPORT = "ERROR: Unable to receive report from server.";
    private static final String ERROR_UNKNOWN = "ERROR: Unable to connect to server.";
    private static final String ERROR_UNFINISHED = "Report is still being analyzed.";

    private ResultsListRVAdapter mResultsRVAdapter;
    private ProgressBar mpbResultsRV;
    private String mClicked; // item recently clicked in recycler view

    public static final String ACTION_BAR_TITLE = "AB_TITLE";

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

        requestResultsList();

        getSupportActionBar().setTitle(getString(R.string.results_actionbar_title));

        initResultsList();
    }

    private void requestResultsList(){
        Intent listIntent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, "request list");
        bundle.putString(SocketService.ACTION_KEY, ACTION_VIEW_RESULTS);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        listIntent.putExtras(bundle);
        startService(listIntent);
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
        mResultsRVAdapter = new ResultsListRVAdapter(this, this);
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
        mResultsRVAdapter.updateItems(testList, testList, testBitmaps());
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

                        // parse result titles from ids
                        ArrayList<String> idList = new ArrayList<>();
                        ArrayList<String> nameList = new ArrayList<>();
                        for(String result : resultList){
                            String[] split = result.split("@");
                            if(split.length == 2){
                                idList.add(split[0]);
                                Log.d(TAG, split[0]);
                                nameList.add(split[1]);
                            }
                        }

                        if (resultList.size() > 0 && !resultList.get(0).equals("")) {
                            mResultsRVAdapter.updateItems(nameList, idList, testBitmaps());
                        } else {
                            ArrayList<String> emptyList = new ArrayList<>();
                            emptyList.add("No results to display");
                            mResultsRVAdapter.updateItems(emptyList, emptyList, testBitmaps());
                        }
                    }
                    // result detail message
                } else if (intent.getStringExtra(SocketService.ACTION_KEY).equals(ACTION_REQUEST_RESULT)) {
                    Log.d(TAG, "result request received");
                    String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
                    if(results.equals(ServerUtils.FAILURE)) {
                        errorToast(ERROR_REPORT);
                    } else if(results.equals(ServerUtils.REPORT_NOT_FINISHED_STRING)) {
                        errorToast(ERROR_UNFINISHED);
                    } else {
                        Intent resultDetailIntent = new Intent(context, ResultDetailController.class);
                        resultDetailIntent.putExtra(SocketService.BROADCAST_KEY, results);
                        resultDetailIntent.putExtra(ACTION_BAR_TITLE, mClicked);
                        startActivity(resultDetailIntent);
                    }
                }
            } else {
                String results = intent.getStringExtra(SocketService.BROADCAST_KEY);
                if (results.getBytes()[0] == ServerUtils.SUCCESS){
                    requestResultsList();
                } else {
                    errorToast(ERROR_UNKNOWN);
                }
            }
        }
    };

    @Override
    public void onResultsClick(String item) {
        Log.d(TAG, "item clicked: " + item);

        String[] split = item.split(",");

        mClicked = split[1];

        mpbResultsRV.setVisibility(View.VISIBLE);

        Intent intent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, split[0]);
        bundle.putString(SocketService.ACTION_KEY, ACTION_REQUEST_RESULT);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        intent.putExtras(bundle);
        startService(intent);
    }

    @Override
    public void onResultsDeleteClick(String item) {
        Log.d(TAG, item);

        deleteAlertDialog(item);
    }

    private void sendDeleteMessage(String resultID){
        String message = ServerUtils.deleteResultFormat(resultID);

        Intent intent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, message);
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

    private void deleteAlertDialog(final String item) {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this, R.style.AnalyzeDialogStyle);

        builder.setTitle("Are you sure you want to delete this report?");

        builder.setPositiveButton("Yes", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                sendDeleteMessage(item);
            }
        });

        builder.setNegativeButton("No", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                dialog.dismiss();
            }
        });

        builder.show();
    }
}
