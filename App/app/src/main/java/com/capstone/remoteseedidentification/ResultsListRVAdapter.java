package com.capstone.remoteseedidentification;

import android.graphics.Bitmap;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import java.util.ArrayList;

/**
 * Created by Alex on 3/17/2018.
 */

public class ResultsListRVAdapter extends RecyclerView.Adapter<ResultsListRVAdapter.ViewHolder> {

    private ArrayList<String> mResultsList;
    private ArrayList<Bitmap> mThumbList;
    private OnResultsClickListener mClickListener;

    public interface OnResultsClickListener{
        void onResultsClick(String item);
    }

    class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener {

        private TextView mTextView;
        private ImageView mImageView;

        public ViewHolder(View itemView) {
            super(itemView);
            mTextView = itemView.findViewById(R.id.tv_results_rv_item);
            mTextView.setOnClickListener(this);

            mImageView = itemView.findViewById(R.id.iv_results_thumbnail_view);
            mImageView.setOnClickListener(this);
        }

        public void bind(String item, Bitmap bitmap){
            mTextView.setText(item);
            mImageView.setImageBitmap(bitmap);
        }

        @Override
        public void onClick(View v) {
            String item = mResultsList.get(getAdapterPosition());
            mClickListener.onResultsClick(item);
        }
    }

    public ResultsListRVAdapter(OnResultsClickListener clickListener){
        mClickListener = clickListener;
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

    public void updateItems(ArrayList<String> items, ArrayList<Bitmap> bitmaps){
        mResultsList = items;
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
