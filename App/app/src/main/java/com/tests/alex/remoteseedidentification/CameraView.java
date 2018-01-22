package com.tests.alex.remoteseedidentification;

import android.content.Context;
import android.graphics.SurfaceTexture;
import android.hardware.Camera;
import android.view.SurfaceView;
import android.view.ViewGroup;
import android.view.SurfaceHolder;

import java.io.IOException;
import java.util.List;

/**
 * Created by Alex on 1/20/2018.
 */

public class CameraView extends SurfaceView implements SurfaceHolder.Callback {

    private SurfaceHolder mHolder;
    private Camera mCamera;

    CameraView(Context context, Camera camera){
        super(context);
        mCamera = camera;

        mHolder = getHolder();
        mHolder.addCallback(this);
    }

    @Override
    public void surfaceCreated(SurfaceHolder surfaceHolder) {

        try{
            mCamera.setPreviewDisplay(surfaceHolder);
            mCamera.startPreview();
        } catch (IOException e) {
            //e.printStackTrace();
        }
    }

    @Override
    public void surfaceChanged(SurfaceHolder surfaceHolder, int i, int i1, int i2) {

        if(mHolder.getSurface() == null){
            return;
        }

        try{
            mCamera.stopPreview();
        }catch (Exception e){
            //ignore
        }

        try{
            mCamera.setPreviewDisplay(mHolder);
            mCamera.startPreview();
        }catch (Exception e){
            e.printStackTrace();
        }
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder surfaceHolder) {

    }

    @Override
    protected void onLayout(boolean b, int i, int i1, int i2, int i3) {

    }
}
