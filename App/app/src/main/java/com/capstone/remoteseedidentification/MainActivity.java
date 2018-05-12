package com.capstone.remoteseedidentification;

import android.Manifest;
import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.hardware.Camera;
import android.net.Uri;
import android.os.Environment;
import android.provider.MediaStore;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v4.content.FileProvider;
import android.support.v4.content.LocalBroadcastManager;
import android.support.v4.widget.DrawerLayout;
import android.support.v7.app.ActionBarDrawerToggle;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.MenuItem;
import android.view.View;
import android.widget.AdapterView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.util.ArrayList;


public class MainActivity extends AppCompatActivity implements NavDrawerRVAdapter.onNavDrawerItemClickListener {

    private final static String TAG = "MainActivity";

    final static int RESULT_LOAD_IMAGE = 1;
    final static int RESULT_CAMERA_IMAGE = 2;
    final static int CAMERA_PERMISSION_REQUEST = 50;

    private Camera mCamera;
    private CameraView mCameraView;
    private ArrayList<String> mNavData;
    private DrawerLayout mDrawerLayout;
    private ListView mDrawerView;
    private ActionBarDrawerToggle mDrawerToggle;
    private AlertDialog mADSendImage;

    //testing image capture
    private ImageButton mCaptureButton;
    private ImageView mThumbView;

    //image data
    private byte[] mByteImage;
    private String mImagePath;

    //nav drawer recycler view
    private RecyclerView mNavRV;
    private NavDrawerRVAdapter mNavAdapter;

    private String mCurrentImagePath;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mBroadcastManager = LocalBroadcastManager.getInstance(this);
        IntentFilter intentFilter = new IntentFilter();
        intentFilter.addAction(BROADCAST_ACTION);
        mBroadcastManager.registerReceiver(mBroadcastReceiver, intentFilter);

        checkPermissions();

        mThumbView = findViewById(R.id.thumb_view);
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
                    //initCamera();
                }
                break;
        }
    }

    // asks user for permissions needed in the app
    private void checkPermissions(){
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED ||
                ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA, Manifest.permission.WRITE_EXTERNAL_STORAGE},
                    CAMERA_PERMISSION_REQUEST);
        }
    }

    private void initCamera(){
            mCamera = getCameraInstance();
            mCamera.setDisplayOrientation(90);

            mCameraView = new CameraView(this, mCamera);
            mCameraView.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    mCamera.autoFocus(null);
                    Log.d(TAG, "frameLayout onClick");
                }
            });
            //FrameLayout frameLayout = findViewById(R.id.cam_view);
            //frameLayout.addView(mCameraView);
    }

    @Override
    public void onNavDrawerItemClick(String item) {
        if(item.equals(getString(R.string.nav_gallery))) {
            //getImageFromGallery();
            analyzeAlertDialog();
        }
        else if(item.equals(getString(R.string.nav_results))){
            goResults();
        }
        else if(item.equals(getString(R.string.nav_login))) {
            goLogin();
        }
    }

    //onClick listener for navigation drawer items
    private class DrawerItemClickListener implements ListView.OnItemClickListener{

        @Override
        public void onItemClick(AdapterView<?> parent, View view, int position, long id) {
            String viewText = (String)((TextView)view).getText();

            if(viewText.equals(getResources().getString(R.string.nav_gallery))) {
                getImageFromGallery();
                mDrawerLayout.closeDrawers();
                mDrawerToggle.syncState();
            }
            else if(viewText.equals(getResources().getString(R.string.nav_results))){
                goResults();
            }
            else if(viewText.equals(getResources().getString(R.string.nav_login))) {
                goLogin();
            }
        }
    }

    public void goLogin(){
        Intent intent = new Intent(this, LoginController.class);

        startActivity(intent);
    }

    public void doLogout(View v){
        Intent stopService = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_MESSAGE_KEY, SocketService.RESET);
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        stopService.putExtras(bundle);
        startService(stopService);

        Intent loginIntent = new Intent(this, LoginController.class);
        startActivity(loginIntent);
    }

    private void goResults(){
        Intent intent = new Intent(this, ResultsController.class);

        startActivity(intent);
    }

    // overload to support calling from button in layout
    public void goResults(View v){
        goResults();
    }

    public void takePicture(View v){

        //using jpg because raw is not supported on every phone
        mCamera.takePicture(null, null, new Camera.PictureCallback() {
            @Override
            public void onPictureTaken(byte[] data, Camera camera) {
                mByteImage = data;
                mImagePath = imageToFile("tempImage.png", data);
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
            if(reqCode == RESULT_LOAD_IMAGE) {
                try {
                    Uri imageUri = data.getData();
                    InputStream imageStream = getContentResolver().openInputStream(imageUri);
                    Bitmap selectedImage = BitmapFactory.decodeStream(imageStream);
                    mThumbView.setImageBitmap(selectedImage);
                    //mCameraView.setVisibility(View.INVISIBLE);
                    //get image from gallery as a byte array for sending
                    mByteImage = getBytes(getContentResolver().openInputStream(imageUri));
                    mImagePath = imageToFile("tempImage.png", mByteImage);

                    initConfirmation();

                } catch (FileNotFoundException e) {
                    e.printStackTrace();
                }
            } else if(reqCode == RESULT_CAMERA_IMAGE){
                Bitmap image = BitmapFactory.decodeFile(mCurrentImagePath);

                Matrix matrix = new Matrix();
                matrix.postRotate(90);
                Bitmap rotated = Bitmap.createBitmap(image, 0, 0, image.getWidth(),
                        image.getHeight(), matrix, true);

                mThumbView.setImageBitmap(rotated);

                ByteBuffer byteBuffer = ByteBuffer.allocate(image.getRowBytes() * image.getHeight());
                image.copyPixelsToBuffer(byteBuffer);
                //mByteImage = byteBuffer.array();
                mByteImage = fileToBytes(mCurrentImagePath);
                mImagePath = mCurrentImagePath;

                initConfirmation();
            }
        }
    }

    //https://stackoverflow.com/questions/10296734/image-uri-to-bytesarray
    private byte[] getBytes(InputStream inputStream){
        Log.d(TAG, "getting bytes");
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
        findViewById(R.id.bt_main_analyze).setVisibility(View.INVISIBLE);
        findViewById(R.id.bt_main_results).setVisibility(View.INVISIBLE);
        findViewById(R.id.bt_main_logout).setVisibility(View.INVISIBLE);
        //mCaptureButton.setVisibility(View.INVISIBLE);
        mThumbView.setVisibility(View.VISIBLE);
    }

    public void doImageConf(View v){
        switch(v.getId()){
            case R.id.button_conf_accept:
                sendImage();
                break;

            default:
                Log.e("doImageConf", "Unknown id: " + v.getId() );
                break;
        }

        //restart camera preview
        //set visibility appropriately
       // mCamera.startPreview();
        //mCameraView.setVisibility(View.VISIBLE);
        //mCaptureButton.setVisibility(View.VISIBLE);
        findViewById(R.id.bt_main_analyze).setVisibility(View.VISIBLE);
        findViewById(R.id.bt_main_results).setVisibility(View.VISIBLE);
        findViewById(R.id.bt_main_logout).setVisibility(View.VISIBLE);
        mThumbView.setVisibility(View.INVISIBLE);
        findViewById(R.id.button_conf_accept).setVisibility(View.GONE);
        findViewById(R.id.button_conf_deny).setVisibility(View.GONE);
    }

    private void sendImage(){
        Log.d(TAG, "starting send image");
        Log.d(TAG, String.valueOf(mByteImage.length));

        // show dialog of sending progress
        sendImageAlertDialog();

        Intent intent = new Intent(this, SocketService.class);
        Bundle bundle = new Bundle();
        bundle.putString(SocketService.SEND_IMAGE_KEY, mImagePath);
        bundle.putString(SocketService.SEND_MESSAGE_KEY, "sendingimage");
        bundle.putString(SocketService.OUTBOUND_KEY, BROADCAST_ACTION);
        intent.putExtras(bundle);
        startService(intent);
    }

    public final static String BROADCAST_ACTION = "mainActivity";
    private LocalBroadcastManager mBroadcastManager;
    private BroadcastReceiver mBroadcastReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            Toast toast;

            Log.d(TAG, "main receiving");

            mADSendImage.dismiss();

            String response = intent.getStringExtra(SocketService.BROADCAST_KEY);
            switch (response){
                case ServerUtils.SUCCESS_STRING:
                    toast = Toast.makeText(getApplicationContext(), "Image Sent", Toast.LENGTH_LONG);
                    toast.show();
                    break;
                case ServerUtils.FAILURE:
                    toast = Toast.makeText(getApplicationContext(), "Image failed to send", Toast.LENGTH_LONG);
                    toast.show();
                    break;
                default:
                    Log.d(TAG, "UNKNOWN return from server");
            }
        }
    };

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if(mDrawerToggle.onOptionsItemSelected(item)){
            return true;
        }
        switch (item.getItemId()) {

            default:
                return super.onOptionsItemSelected(item);
        }
    }

    public static String imageToFile(String fileName, byte[] data){
        File photo = new File(Environment.getExternalStorageDirectory(), fileName);

        if(photo.exists()){
            photo.delete();
        }

        try{
            FileOutputStream fos = new FileOutputStream(photo.getPath());
            fos.write(data);
            fos.close();
        }catch (IOException e){
            e.printStackTrace();
        }

        return photo.getAbsolutePath();
    }

    public static byte[] fileToBytes(String fileName){
        File photo = new File(fileName);

        try {
            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
            InputStream inputStream = new FileInputStream(photo);
            byte[] buffer = new byte[32768];
            while(inputStream.read(buffer) != -1) {
                byteArrayOutputStream.write(buffer);
            }
            inputStream.close();
            return byteArrayOutputStream.toByteArray();
        }catch (FileNotFoundException e){
            e.printStackTrace();
        }catch (IOException e){
            e.printStackTrace();
        }

        return null;
    }

    private void analyzeAlertDialog() {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this, R.style.AnalyzeDialogStyle);

        builder.setTitle("Choose");
        builder.setItems(R.array.analyze_items, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                switch (which){
                    case 0:
                        startCameraIntent();
                        break;

                    case 1:
                        getImageFromGallery();
                        break;

                    default:
                        Log.d(TAG, "Unknown item clicked");
                }
            }
        });

        builder.show();
    }

    private void sendImageAlertDialog() {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this, R.style.AnalyzeDialogStyle);

        LayoutInflater inflater = this.getLayoutInflater();

        builder.setView(inflater.inflate(R.layout.dialog_send_image, null));

        mADSendImage = builder.create();
        mADSendImage.show();
    }

    private void accountAlertDialog() {
        final AlertDialog.Builder builder = new AlertDialog.Builder(this, R.style.AnalyzeDialogStyle);

        builder.setTitle("Choose");
        builder.setItems(R.array.account_items, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                switch (which){
                    // change password
                    case 0:
                        switchChangePassword();
                        break;

                    default:
                        Log.d(TAG, "Unknown item clicked");
                }
            }
        });

        builder.show();
    }

    private void switchChangePassword(){
        Button analyze = findViewById(R.id.bt_main_analyze);
        Button results = findViewById(R.id.bt_main_results);
        Button account = findViewById(R.id.bt_main_account);
        Button logout = findViewById(R.id.bt_main_logout);
        analyze.setVisibility(analyze.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        results.setVisibility(results.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        account.setVisibility(account.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        logout.setVisibility(logout.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);

        Button changepw = findViewById(R.id.bt_main_changepw);
        Button cancel = findViewById(R.id.bt_main_cancel);
        EditText oldpw = findViewById(R.id.et_main_oldpw);
        EditText newpw = findViewById(R.id.et_main_newpw);
        EditText newpwconf = findViewById(R.id.et_main_newpw_conf);
        changepw.setVisibility(changepw.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        cancel.setVisibility(cancel.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        oldpw.setVisibility(oldpw.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        newpw.setVisibility(newpw.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
        newpwconf.setVisibility(newpwconf.getVisibility() == View.VISIBLE ? View.INVISIBLE : View.VISIBLE);
    }

    public void switchChangePassword(View v) {
        switchChangePassword();
    }

    public void doChangePW(View v){

    }

    // overload to support onClick from button in layout
    public void anaylzeAlertDialog(View v){
        analyzeAlertDialog();
    }

    // overload to support onClick from button in layout
    public void accountAlertDialog(View v){
        accountAlertDialog();
    }


    private void startCameraIntent(){
        Intent intent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);

        if(intent.resolveActivity(getPackageManager()) != null){
            File photoFile = createImageFile("tempSeedImage");
            if(photoFile != null) {
                Uri photoUri = FileProvider.getUriForFile(this,
                        "com.example.android.fileprovider",
                        photoFile);
                intent.putExtra(MediaStore.EXTRA_OUTPUT, photoUri);
            }
            startActivityForResult(intent, RESULT_CAMERA_IMAGE);
        }
    }

    private File createImageFile(String fileName) {
        File image = null;
        File storageDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);

        try {
            image = File.createTempFile(fileName, ".png", storageDir);
        } catch (IOException e){
            e.printStackTrace();
        }

        mCurrentImagePath = image.getAbsolutePath();
        return image;
    }
}
