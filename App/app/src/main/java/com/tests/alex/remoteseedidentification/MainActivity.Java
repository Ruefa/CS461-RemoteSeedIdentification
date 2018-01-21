package com.tests.alex.remoteseedidentification;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        int camID = 5; //change this
        CameraControl.safeCameraOpen(camID);
    }
}