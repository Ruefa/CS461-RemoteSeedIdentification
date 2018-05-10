package com.capstone.remoteseedidentification;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.support.constraint.ConstraintLayout;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;

import com.github.mikephil.charting.charts.PieChart;
import com.github.mikephil.charting.components.Description;
import com.github.mikephil.charting.components.Legend;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.PieData;
import com.github.mikephil.charting.data.PieDataSet;
import com.github.mikephil.charting.data.PieEntry;
import com.github.mikephil.charting.formatter.PercentFormatter;
import com.itextpdf.text.Image;
import com.itextpdf.text.pdf.PdfWriter;
import com.jjoe64.graphview.GraphView;
import com.jjoe64.graphview.ValueDependentColor;
import com.jjoe64.graphview.series.BarGraphSeries;
import com.jjoe64.graphview.series.DataPoint;

import org.w3c.dom.Document;

import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.net.URI;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

public class ResultDetailController extends AppCompatActivity {
    private final static String TAG = "ResultDetailController";

    private GraphView mGraphView;
    private PieChart mPieChart;
    private ImageView ivResult;
    private Map<String, String> seedNames;

    // pie chart settings
    private static final int PC_TEXT_SIZE = 14;
    private static final String PC_TITLE = "Seed Distribution";

    private static final String PDF_PATH_TITLE = "Result_Detail";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result_detail);

        seedNames = new HashMap<String, String>(){};
        seedNames.put("rc", "Red Clover");
        seedNames.put("flax", "Flax");
        seedNames.put("tf", "Tall Fescue");
        seedNames.put("wheat", "Wheat");
        seedNames.put("prg", "");

        ivResult = findViewById(R.id.iv_result_detail);

        initData();

        // change to result date later
        getSupportActionBar().setTitle("4/25/2018 15:00");
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.result_detail_menu, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case R.id.action_share:
                sharePDF();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    private void initData(){
        // get results from intent that started the activity
        String results = getIntent().getStringExtra(SocketService.BROADCAST_KEY);
        Log.d(TAG, results);

        String resultArray[] = results.split("\n");
        Log.d(TAG, Arrays.toString(resultArray));

        setImageDisplay(resultArray[resultArray.length-1]);

        List<String> labels = new LinkedList<>();
        List<String> seedPercentage = new LinkedList<>();
        List<Integer> colors = new LinkedList<>();
        int seedCount = 0;
        // last index is the image so we want to ignore that.
        for(int i=0; i<resultArray.length-1; i++){
            String[] resultSplit = resultArray[i].split(",");
            String[] nameSplit = resultSplit[0].split(":");
            labels.add(nameSplit[0]);
            seedPercentage.add(nameSplit[1]);
            colors.add(Color.parseColor(resultSplit[2]));
            seedCount += Integer.valueOf(resultSplit[1]);
        }

        initPieChart(labels, seedPercentage, colors);
    }

    private void setImageDisplay(String fileName){
        byte[] imageBytes = MainActivity.fileToBytes(fileName);
        Bitmap thumbBitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);
        ivResult.setImageBitmap(thumbBitmap);
    }

    private void sharePDF(){
        Bitmap screen = getScreenBitmap();
        ((ImageView)findViewById(R.id.iv_result_detail)).setImageBitmap(screen);

        Uri uri = bitmapToUri(screen);
        Intent share = new Intent();
        share.setAction(Intent.ACTION_SEND);
        share.setType("application/pdf");
        share.putExtra(Intent.EXTRA_STREAM, uri);
        startActivity(share);
    }

    // gets bitmap of current activities screen display
    private Bitmap getScreenBitmap(){
        Bitmap screen;

        LayoutInflater inflater = (LayoutInflater) this.getSystemService(LAYOUT_INFLATER_SERVICE);
        ConstraintLayout root = (ConstraintLayout) inflater.inflate(R.layout.activity_result_detail, null);
        root.setDrawingCacheEnabled(true);
        screen = getBitmapFromView(this.getWindow().findViewById(R.id.result_detail_root));

        return screen;
    }

    private Bitmap getBitmapFromView(View view){
        Bitmap returnedBitmap = Bitmap.createBitmap(view.getWidth(), view.getHeight(), Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(returnedBitmap);
        Drawable drawable = view.getBackground();
        if(drawable != null){
            drawable.draw(canvas);
        }else{
            canvas.drawColor(Color.WHITE);
        }

        view.draw(canvas);

        return returnedBitmap;
    }

    private Uri bitmapToUri(Bitmap bitmap){
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, bytes);
        String path = MediaStore.Images.Media.insertImage(this.getContentResolver(), bitmap,
                PDF_PATH_TITLE, null);
        return Uri.parse(path);
    }

    private void bitmapToPDF(Bitmap bitmap){
        com.itextpdf.text.Document document = new com.itextpdf.text.Document();
        String dirPath = android.os.Environment.getExternalStorageDirectory().toString();
        try {
            PdfWriter.getInstance(document, new FileOutputStream(dirPath + "/" + PDF_PATH_TITLE + ".pdf"));
            document.open();
            Image img = Image.getInstance(dirPath + "/" + PDF_PATH_TITLE + ".png");
            //img = Image.getInstance(bitmap);

            float scalar = ((document.getPageSize().getWidth() - document.leftMargin()
            - document.rightMargin() - 0) / img.getWidth()) * 100;
            img.scalePercent(scalar);
            img.setAlignment(Image.ALIGN_CENTER | Image.ALIGN_TOP);
            document.add(img);
            document.close();
        } catch (Exception e){
            e.printStackTrace();
        }
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
    private void initPieChart(List<String> labels, List<String> seedPercentage, List<Integer> colors){
        mPieChart = findViewById(R.id.pc_seed_makeup);
        List<Integer> colorsToDisplay = new LinkedList<>();

        // create test data
        List<PieEntry> entries = new ArrayList<>();
        for(int i=0; i<seedPercentage.size(); i++){
            if(Float.valueOf(seedPercentage.get(i)) > 0) {
                entries.add(new PieEntry(Float.valueOf(seedPercentage.get(i)) * 100,
                        seedNames.get(labels.get(i))));
                colorsToDisplay.add(colors.get(i));
            }
        }
        /*entries.add(new PieEntry(Float.valueOf(seedPercentage.get(2))*100, "Tall Fescue"));
        entries.add(new PieEntry(Float.valueOf(seedPercentage.get(3))*100, "Wheat"));
        entries.add(new PieEntry(Float.valueOf(seedPercentage.get(1))*100, "Flax"));
        entries.add(new PieEntry(Float.valueOf(seedPercentage.get(0))*100, "Red Clover"));*/

        // create data set and add to pie chart
        // label hidden
        PieDataSet dataSet = new PieDataSet(entries, "");
        // colors appear in same order as entries
        dataSet.setColors(colorsToDisplay);
        /*dataSet.setColors(getResources().getColor(R.color.blue),
                getResources().getColor(R.color.light_orange),
                getResources().getColor(R.color.gold),
                getResources().getColor(R.color.light_red));*/
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
