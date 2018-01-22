package com.tests.alex.remoteseedidentification;

import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.Camera;
import android.util.Log;

/**
 * Created by Alex on 1/19/2018.
 */

public class CameraControl {

    private static Camera mCamera;

    /*
    needs to be changed later
     */
    public static boolean safeCameraOpen(int id){
        boolean camOpened = false;

        try{
            releaseCameraAndPreview();
            mCamera = Camera.open(id);
            camOpened = (mCamera != null);
        }catch(Exception e){
            Log.e("Hello", "Failed to open Camera"); //change this
            e.printStackTrace();
        }

        return camOpened;
    }



    private static void releaseCameraAndPreview(){
        if(mCamera != null){
            mCamera.release();
            mCamera = null;
        }
    }
}
