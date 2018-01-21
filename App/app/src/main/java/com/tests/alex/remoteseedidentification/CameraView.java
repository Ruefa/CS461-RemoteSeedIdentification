package com.tests.alex.remoteseedidentification;

import android.content.Context;
import android.hardware.Camera;
import android.view.SurfaceView;
import android.view.ViewGroup;
import android.view.SurfaceHolder;

import java.io.IOException;
import java.util.List;

/**
 * Created by Alex on 1/20/2018.
 */

public class CameraView extends ViewGroup implements SurfaceHolder.Callback {

    private SurfaceView mSurfaceView;
    private SurfaceHolder mHolder;
    private Camera mCamera;
    private List<Camera.Size> mSupportedPreviewSizes;

    CameraView(Context context){
        super(context);

        mSurfaceView = new SurfaceView(context);
        addView(mSurfaceView);

        mHolder = mSurfaceView.getHolder();
        mHolder.addCallback(this);
    }


    public void setCamera(Camera camera){
        if(mCamera == camera) { return; }

        stopPreviewAndFreeCamera();

        mCamera = camera;

        if(mCamera != null){
            List<Camera.Size> localSizes = mCamera.getParameters().getSupportedPreviewSizes();
            mSupportedPreviewSizes = localSizes;
            requestLayout();

            try{
                mCamera.setPreviewDisplay(mHolder);
            }catch (IOException e){
                e.printStackTrace();
            }

            mCamera.startPreview();
        }
    }

    @Override
    public void surfaceCreated(SurfaceHolder surfaceHolder) {

    }

    @Override
    public void surfaceChanged(SurfaceHolder surfaceHolder, int i, int i1, int i2) {
        Camera.Parameters parameters = mCamera.getParameters();
        parameters.setPreviewSize(mPreviewSize.width, mPreviewSize.height);
        requestLayout();
        mCamera.setParameters(parameters);

        mCamera.startPreview();
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder surfaceHolder) {
        
    }

    @Override
    protected void onLayout(boolean b, int i, int i1, int i2, int i3) {

    }
}
