package com.capstone.remoteseedidentification;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.support.v4.app.ActivityCompat;
import android.support.v4.content.ContextCompat;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;

public class LoginController extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.INTERNET) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.INTERNET}, 0);
        }
    }

    public void doLogin(View v){
        boolean loginSuccess = true;

        //open socket with server
        ServerAsyncTask task = new ServerAsyncTask();
        task.execute("");
        //task.sendMessage("test");


        if(loginSuccess) {
            goMain();
        }
    }

    private void goMain(){
        Intent intent = new Intent(this, MainActivity.class);

        startActivity(intent);
    }
}
