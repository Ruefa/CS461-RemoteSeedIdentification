package com.capstone.remoteseedidentification;

import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Matrix;
import android.graphics.drawable.Drawable;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.support.constraint.ConstraintLayout;
import android.support.v4.content.FileProvider;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

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
import java.io.File;
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

        // translate seed names from server results to full name
        seedNames = new HashMap<String, String>(){};
        seedNames.put("rc", "Red Clover");
        seedNames.put("flax", "Flax");
        seedNames.put("tf", "Tall Fescue");
        seedNames.put("wheat", "Wheat");
        seedNames.put("prg", "");

        ivResult = findViewById(R.id.iv_result_detail);

        initData();
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

        // set action bar title
        getSupportActionBar().setTitle(getIntent().getStringExtra(ResultsController.ACTION_BAR_TITLE));

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

        initPieChart(labels, seedPercentage, colors, seedCount);
    }

    private void setImageDisplay(String fileName){
        byte[] imageBytes = MainActivity.fileToBytes(fileName);
        Bitmap thumbBitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.length);

        Matrix matrix = new Matrix();
        matrix.postRotate(90);
        Bitmap rotated = Bitmap.createBitmap(thumbBitmap, 0, 0, thumbBitmap.getWidth(),
                thumbBitmap.getHeight(), matrix, true);

        ivResult.setImageBitmap(rotated);
    }

    private void sharePDF(){
        // get bitmap image of screen
        Bitmap screen = getScreenBitmap();
        // save bitmap to pdf and get path
        String filePath = bitmapToPDF(screen);
        // convert pdf file to uri
        File pdfFile = new File(filePath);
        Uri uri = FileProvider.getUriForFile(this, "com.example.android.fileprovider", pdfFile);
        // share pdf using intent
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

    // extracts bitmap from view
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

    // converts bitmap to pdf
    // returns string of pdf path
    private String bitmapToPDF(Bitmap bitmap){
        com.itextpdf.text.Document document = new com.itextpdf.text.Document();
        String dirPath = android.os.Environment.getExternalStorageDirectory().toString();
        String pdfFileName = dirPath + "/" + PDF_PATH_TITLE + ".pdf";
        String imageFileName = dirPath + "/" + PDF_PATH_TITLE + ".png";

        try {
            // open pdf file for writing
            PdfWriter.getInstance(document, new FileOutputStream(pdfFileName));
            document.open();
            // save bitmap to png file. must convert Bitmap to Image this way
            FileOutputStream outputStream = new FileOutputStream(imageFileName);
            bitmap.compress(Bitmap.CompressFormat.PNG, 30, outputStream);
            outputStream.flush();
            outputStream.close();
            // open saved bitmap as Image object
            Image img = Image.getInstance(imageFileName);

            // properly scale image
            float scalar = ((document.getPageSize().getWidth() - document.leftMargin()
            - document.rightMargin() - 0) / img.getWidth()) * 100;
            img.scalePercent(scalar);
            img.setAlignment(Image.ALIGN_CENTER | Image.ALIGN_TOP);

            document.add(img);
            document.close();
        } catch (Exception e){
            e.printStackTrace();
        }

        return pdfFileName;
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
    private void initPieChart(List<String> labels, List<String> seedPercentage, List<Integer> colors, int seedCount){
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

        // create data set and add to pie chart
        // label hidden
        PieDataSet dataSet = new PieDataSet(entries, "");
        // colors appear in same order as entries
        dataSet.setColors(colorsToDisplay);
        dataSet.setValueTextSize(PC_TEXT_SIZE);
        // set format of values to percentages
        dataSet.setValueFormatter(new PercentFormatter());
        // set value label position
        //dataSet.setXValuePosition(PieDataSet.ValuePosition.OUTSIDE_SLICE);
        //dataSet.setYValuePosition(PieDataSet.ValuePosition.OUTSIDE_SLICE);
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

        // set center text on pie chart
        mPieChart.setDrawCenterText(true);
        mPieChart.setCenterText(String.valueOf(seedCount) + "\nseeds");
        mPieChart.setCenterTextSize(PC_TEXT_SIZE);

        // hide description
        Description description = new Description();
        description.setText("");
        mPieChart.setDescription(description);

        mPieChart.invalidate(); // refresh
    }
}
