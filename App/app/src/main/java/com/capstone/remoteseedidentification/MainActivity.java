package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.hardware.Camera;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.widget.DrawerLayout;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.FrameLayout;
import android.widget.ListView;

import java.util.List;


public class MainActivity extends AppCompatActivity {

    private Camera mCamera;
    private CameraView mCameraView;
    private String[] mNavData;
    private DrawerLayout mDrawerLayout;
    private ListView mDrawerView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mCamera = getCameraInstance();
        mCamera.setDisplayOrientation(90);

        mCameraView = new CameraView(this, mCamera);
        FrameLayout frameLayout = findViewById(R.id.cam_view);
        frameLayout.addView(mCameraView);

        initNavigation();
    }

    private Camera getCameraInstance(){
        Camera cam = null;

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 50);

        //sleep to give time to accept permissions or app will crash (only on first run)
        //android.os.SystemClock.sleep(5000);

        try{
            cam = Camera.open(0);
        }
        catch (Exception e){
            e.printStackTrace();
        }

        return cam;
    }

    private void initNavigation(){
        mNavData = dummyData(10);
        mDrawerLayout = findViewById(R.id.drawer_layout);
        mDrawerView = findViewById(R.id.navigation_list_view);

        mDrawerView.setAdapter(new ArrayAdapter<>(this, R.layout.nav_text_view, mNavData));

        mDrawerView.setOnItemClickListener(new DrawerItemClickListener());
    }

    private class DrawerItemClickListener implements ListView.OnItemClickListener{

        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            goLogin();
        }
    }

    private String[] dummyData(int numData){

        String[] data = new String[numData];

        for(int i=0; i<data.length; i++){
            data[i] = String.valueOf(i+1);
        }

        return data;
    }

    public void goLogin(){
        Intent intent = new Intent(this, LoginController.class);

        startActivity(intent);
    }
}
