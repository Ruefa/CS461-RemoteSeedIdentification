package com.capstone.remoteseedidentification;

import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.EditText;

public class RegisterController extends AppCompatActivity {

    private static final String TAG = "RegisterController";

    private EditText etUser, etPass;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_register);

        etUser = findViewById(R.id.et_register_username);
        etPass = findViewById(R.id.et_register_pass);
    }

    public void doRegister(View v){
        final String message;

        message = "a" + etUser.getText().toString() + "@" + etPass.getText().toString();

        ServerAsyncTask asyncTask = new ServerAsyncTask(mCallback);
        asyncTask.execute(message);
    }

    private ServerUtils.MessageCallback mCallback = new ServerUtils.MessageCallback() {
        @Override
        public void callbackMessageReceiver(String message) {
            Log.d(TAG, message);
        }
    };
}
