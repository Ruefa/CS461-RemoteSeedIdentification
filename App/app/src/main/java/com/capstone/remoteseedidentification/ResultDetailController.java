package com.capstone.remoteseedidentification;

import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;

import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

public class ResultDetailController extends AppCompatActivity {
    private final static String TAG = "ResultDetailController";

    private GraphView mGraphView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result_detail);

        // change to result date later
        getSupportActionBar().setTitle(getString(R.string.result_detail_actionbar_title));

        initResultsGraph();
    }

    private void initResultsGraph(){
        mGraphView = findViewById(R.id.graph_results);

        BarGraphSeries<DataPoint> series = new BarGraphSeries<>(new DataPoint[] {
                new DataPoint(0, 15),
                new DataPoint(1, 20)
        });
        mGraphView.addSeries(series);

        //styling
        series.setValueDependentColor(new ValueDependentColor<DataPoint>() {
            @Override
            public int get(DataPoint data) {
                return Color.rgb((int) data.getX()*255/4, (int) Math.abs(data.getY()*255/6), 100);
            }
        });
        series.setSpacing(2);

        series.setDrawValuesOnTop(true);
        series.setValuesOnTopColor(Color.RED);
        mGraphView.getViewport().setYAxisBoundsManual(true);
        mGraphView.getViewport().setMaxY(100);
        mGraphView.getViewport().setXAxisBoundsManual(true);
        mGraphView.getViewport().setMaxX(4);
        mGraphView.getGridLabelRenderer().setHorizontalAxisTitle("Seed Type");
        mGraphView.getGridLabelRenderer().setVerticalAxisTitle("Percent present");
        mGraphView.getGridLabelRenderer().setPadding(30);
    }
}
