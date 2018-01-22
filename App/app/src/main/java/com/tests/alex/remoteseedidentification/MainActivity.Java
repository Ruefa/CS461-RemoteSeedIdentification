package com.tests.alex.remoteseedidentification;

import android.hardware.Camera;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.FrameLayout;

public class MainActivity extends AppCompatActivity {

    private Camera mCamera;
    private CameraView mCameraView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mCamera = CameraControl.getCameraInstance();

        mCameraView = new CameraView(this, mCamera);
        FrameLayout frameLayout = findViewById(R.id.cam_view);
        frameLayout.addView(mCameraView);
    }
}