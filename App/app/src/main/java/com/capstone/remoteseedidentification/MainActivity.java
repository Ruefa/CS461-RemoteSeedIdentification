package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.Camera;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.FrameLayout;
import android.widget.TextView;


public class MainActivity extends AppCompatActivity {

    private Camera mCamera;
    private CameraView mCameraView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mCamera = getCameraInstance();
        mCamera.setDisplayOrientation(90);

        mCameraView = new CameraView(this, mCamera);
        FrameLayout frameLayout = findViewById(R.id.cam_view);
        frameLayout.addView(mCameraView);
    }

    private Camera getCameraInstance(){
        Camera cam = null;

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, 50);

        android.os.SystemClock.sleep(5000);

        try{
            cam = Camera.open(0);
        }
        catch (Exception e){
            e.printStackTrace();
        }

        return cam;
    }
}
