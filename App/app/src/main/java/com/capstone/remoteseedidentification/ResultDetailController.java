package com.capstone.remoteseedidentification;

import android.graphics.Color;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;

import com.github.mikephil.charting.charts.PieChart;
import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.components.Legend;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.PieData;
import com.github.mikephil.charting.data.PieDataSet;
import com.github.mikephil.charting.data.PieEntry;
import com.github.mikephil.charting.formatter.PercentFormatter;
import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

import java.util.ArrayList;
import java.util.List;

public class ResultDetailController extends AppCompatActivity {
    private final static String TAG = "ResultDetailController";

    private GraphView mGraphView;
    private PieChart mPieChart;

    // pie chart settings
    private static final int PC_TEXT_SIZE = 14;
    private static final String PC_TITLE = "Seed Distribution";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result_detail);

        // change to result date later
        getSupportActionBar().setTitle("4/25/2018 15:00");

        initResultsGraph();

        initPieChart();
    }

    // deprecated. now using pie chart
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

    // initializes pie chart with data and themeing
    private void initPieChart(){
        mPieChart = findViewById(R.id.pc_seed_makeup);

        // create test data
        List<PieEntry> entries = new ArrayList<>();
        entries.add(new PieEntry(20.0f, "Seed1"));
        entries.add(new PieEntry(40.0f, "Seed2"));
        entries.add(new PieEntry(30.0f, "Seed3"));
        entries.add(new PieEntry(10.0f, "Seed4"));

        // create data set and add to pie chart
        // label hidden
        PieDataSet dataSet = new PieDataSet(entries, "");
        // colors appear in same order as entries
        dataSet.setColors(getResources().getColor(R.color.blue),
                getResources().getColor(R.color.light_orange),
                getResources().getColor(R.color.gold),
                getResources().getColor(R.color.light_red));
        dataSet.setValueTextSize(PC_TEXT_SIZE);
        // set format of values to percentages
        dataSet.setValueFormatter(new PercentFormatter());
        mPieChart.setData(new PieData(dataSet));

        // center legend text horizontally and set text size
        mPieChart.getLegend().setHorizontalAlignment(Legend.LegendHorizontalAlignment.CENTER);
        mPieChart.getLegend().setTextSize(12);

        // hide labels on pie chart
        mPieChart.setDrawEntryLabels(false);

        // disable hole that is drawn in center of pie char
        //mPieChart.setDrawHoleEnabled(false);
        mPieChart.setHoleRadius(mPieChart.getHoleRadius()-15);
        mPieChart.setTransparentCircleRadius(mPieChart.getTransparentCircleRadius()-15);

        // hide description
        Description description = new Description();
        description.setText("");
        mPieChart.setDescription(description);

        mPieChart.invalidate(); // refresh
    }
}
