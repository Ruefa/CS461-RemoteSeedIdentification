package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.hardware.Camera;
import android.net.Uri;
import android.provider.MediaStore;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.widget.DrawerLayout;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;


public class MainActivity extends AppCompatActivity {

    private Camera mCamera;
    private CameraView mCameraView;
    private ArrayList<String> mNavData;
    private DrawerLayout mDrawerLayout;
    private ListView mDrawerView;

    //testing image capture
    private ImageButton mCaptureButton;
    private ImageView mThumbView;

    //image data
    private byte[] mByteImage;

    final static int RESULT_LOAD_IMAGE = 1;
    final static int CAMERA_PERMISSION_REQUEST = 50;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mThumbView = findViewById(R.id.thumb_view);
        mCaptureButton = findViewById(R.id.button_snap);

        initCamera();

        initNavigation();
    }

    private Camera getCameraInstance(){
        Camera cam = null;

        try {
            cam = Camera.open(0);
        } catch (Exception e) {
            e.printStackTrace();
        }

        return cam;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults){
        switch (requestCode){
            case CAMERA_PERMISSION_REQUEST:
                if(grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED){
                    initCamera();
                }
                break;
        }
    }

    private void initCamera(){
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.CAMERA}, CAMERA_PERMISSION_REQUEST);
        }
        else {
            mCamera = getCameraInstance();
            mCamera.setDisplayOrientation(90);

            mCameraView = new CameraView(this, mCamera);
            FrameLayout frameLayout = findViewById(R.id.cam_view);
            frameLayout.addView(mCameraView);
        }
    }

    private void initNavigation(){
        mNavData = new ArrayList<>();
        mNavData.add(getResources().getString(R.string.nav_gallery));
        mNavData.add(getResources().getString(R.string.nav_results));
        mNavData.add(getResources().getString(R.string.nav_login));

        mDrawerLayout = findViewById(R.id.drawer_layout);
        mDrawerView = findViewById(R.id.navigation_list_view);

        mDrawerView.setAdapter(new ArrayAdapter<>(this, R.layout.nav_text_view, mNavData));

        mDrawerView.setOnItemClickListener(new DrawerItemClickListener());
    }

    private class DrawerItemClickListener implements ListView.OnItemClickListener{

        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            String viewText = (String)((TextView)view).getText();

            if(viewText.equals(getResources().getString(R.string.nav_gallery))) {
                getImageFromGallery();
            }
            else if(viewText.equals(getResources().getString(R.string.nav_results))){
                goResults();
            }
            else if(viewText.equals(getResources().getString(R.string.nav_login))) {
                goLogin();
            }
        }
    }

    //makes dummy strings for testing
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

    private void goResults(){
        Intent intent = new Intent(this, ResultsController.class);

        startActivity(intent);
    }

    public void takePicture(View v){

        //using jpg because raw is not supported on every phone
        mCamera.takePicture(null, null, new Camera.PictureCallback() {
            @Override
            public void onPictureTaken(byte[] data, Camera camera) {
                mByteImage = data;
                Bitmap thumbBitmap = BitmapFactory.decodeByteArray(data, 0, data.length);
                mThumbView.setImageBitmap(thumbBitmap);
                initConfirmation();
            }
        });
    }

    private void getImageFromGallery(){
        Intent getPhotoIntent = new Intent(Intent.ACTION_PICK);
        getPhotoIntent.setType("image/*");
        startActivityForResult(getPhotoIntent, RESULT_LOAD_IMAGE);
    }

    @Override
    protected void onActivityResult(int reqCode, int resultCode, Intent data){
        super.onActivityResult(reqCode, resultCode, data);

        if(resultCode == RESULT_OK){
            try {
                Uri imageUri = data.getData();
                InputStream imageStream = getContentResolver().openInputStream(imageUri);
                //mByteImage = getBytes(imageStream);
                Bitmap selectedImage = BitmapFactory.decodeStream(imageStream);
                mThumbView.setImageBitmap(selectedImage);
                mCameraView.setVisibility(View.INVISIBLE); //remove later
                initConfirmation();
            }
            catch (FileNotFoundException e){
                e.printStackTrace();
            }
        }
    }

    //https://stackoverflow.com/questions/10296734/image-uri-to-bytesarray
    //needs testing. definitely a bug here
    private byte[] getBytes(InputStream inputStream){
        ByteArrayOutputStream byteBuffer = new ByteArrayOutputStream();
        int bufferSize = 1024;
        byte[] buffer = new byte[bufferSize];

        int len = 0;
        try {
            while ((len = inputStream.read(buffer)) != -1) {
                byteBuffer.write(buffer, 0, len);
            }
            return byteBuffer.toByteArray();
        }
        catch (IOException e){
            e.printStackTrace();
            return null;
        }
    }

    private void initConfirmation(){
        Button acc = findViewById(R.id.button_conf_accept);
        Button deny = findViewById(R.id.button_conf_deny);

        acc.setVisibility(View.VISIBLE);
        deny.setVisibility(View.VISIBLE);
        mCaptureButton.setVisibility(View.INVISIBLE);
    }

    public void doImageConf(View v){
        Toast toast;

        switch(v.getId()){
            case R.id.button_conf_accept:
                toast = Toast.makeText(this, "Image Sent", Toast.LENGTH_LONG);
                break;

            case R.id.button_conf_deny:
                toast = Toast.makeText(this, "Image Denied", Toast.LENGTH_LONG);
                break;

            default:
                Log.e("doImageConf", "Unknown id: " + v.getId() );
                return;
        }

        toast.show();

        //restart camera preview
        //set visibility appropriately
        mCamera.startPreview();
        mCameraView.setVisibility(View.VISIBLE);
        mCaptureButton.setVisibility(View.VISIBLE);
        findViewById(R.id.button_conf_accept).setVisibility(View.GONE);
        findViewById(R.id.button_conf_deny).setVisibility(View.GONE);
    }
}
