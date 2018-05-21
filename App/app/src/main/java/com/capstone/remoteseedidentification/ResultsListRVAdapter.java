package com.capstone.remoteseedidentification;

import android.graphics.Bitmap;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.ArrayList;

/**
 * Created by Alex on 3/17/2018.
 */

public class ResultsListRVAdapter extends RecyclerView.Adapter<ResultsListRVAdapter.ViewHolder> {

    private ArrayList<String> mResultsList;
    private ArrayList<String> mIdsList;
    private ArrayList<Bitmap> mThumbList;
    private OnResultsClickListener mClickListener;
    private OnDeleteClickListener mDeleteListener;

    public interface OnResultsClickListener{
        void onResultsClick(String item);
    }

    public interface OnDeleteClickListener{
        void onResultsDeleteClick(String item);
    }

    class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener {

        private TextView mTextView;
        private ImageView mImageView;
        private ImageButton mDeleteButton;

        public ViewHolder(View itemView) {
            super(itemView);
            mTextView = itemView.findViewById(R.id.tv_results_rv_item);
            mTextView.setOnClickListener(this);

            mImageView = itemView.findViewById(R.id.iv_results_thumbnail_view);
            mImageView.setOnClickListener(this);

            mDeleteButton = itemView.findViewById(R.id.bt_results_delete);
            mDeleteButton.setOnClickListener(new View.OnClickListener() {
                @Override
                public void onClick(View v) {
                    mDeleteListener.onResultsDeleteClick(mIdsList.get(getAdapterPosition()));
                }
            });
        }

        public void bind(String item, Bitmap bitmap){
            mTextView.setText(item);
            //mImageView.setImageBitmap(bitmap);
        }

        @Override
        public void onClick(View v) {
            String item = mIdsList.get(getAdapterPosition());
            item += "," + mResultsList.get(getAdapterPosition());
            mClickListener.onResultsClick(item);
        }
    }

    public ResultsListRVAdapter(OnResultsClickListener clickListener, OnDeleteClickListener deleteListener){
        mClickListener = clickListener;
        mDeleteListener = deleteListener;
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        View itemView = inflater.inflate(R.layout.results_rv_item, parent, false);
        return new ResultsListRVAdapter.ViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        holder.bind(mResultsList.get(position), mThumbList.get(position));
    }

    public void updateItems(ArrayList<String> items, ArrayList<String> ids, ArrayList<Bitmap> bitmaps){
        mResultsList = items;
        mIdsList = ids;
        mThumbList = bitmaps;
        notifyDataSetChanged();
    }

    @Override
    public int getItemCount() {
        if(mResultsList != null){
            return mResultsList.size();
        }else {
            return 0;
        }
    }
}
