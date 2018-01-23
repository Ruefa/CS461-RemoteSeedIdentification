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

        TextView debug = findViewById(R.id.debug_view);

        if(checkCameraHardware(this)) {
            mCamera = getCameraInstance();

            mCameraView = new CameraView(this, mCamera);
            FrameLayout frameLayout = findViewById(R.id.cam_view);
            frameLayout.addView(mCameraView);
        }
        else{
            debug.setText("No Camera");
        }
    }

    private Camera getCameraInstance(){
        Camera cam = null;

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED)
            //ask for authorisation
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

    private boolean checkCameraHardware(Context context){
        if(context.getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA)){
            return true;
        }
        else{
            return false;
        }
    }
}
