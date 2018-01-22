package com.tests.alex.remoteseedidentification;

import android.content.Context;
import android.content.pm.PackageManager;
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

        mCamera = getCameraInstance();

        mCameraView = new CameraView(this, mCamera);
        FrameLayout frameLayout = findViewById(R.id.cam_view);
        frameLayout.addView(mCameraView);
    }

    private boolean checkCameraHardware(Context context){
        if(context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA)){
            return true;
        }
        else{
            return false;
        }
    }

    private static Camera getCameraInstance(){
        Camera cam = null;

        try{
            cam = Camera.open();
        }catch (Exception e){
            // Camera not available
        }

        return cam;
    }
}