package com.capstone.remoteseedidentification;

import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.util.ArrayList;

/**
 * Created by Alex on 3/17/2018.
 */

public class ResultsListRVAdapter extends RecyclerView.Adapter<ResultsListRVAdapter.ViewHolder> {

    private ArrayList<String> mResultsList;
    private OnResultsClickListener mClickListener;

    public interface OnResultsClickListener{
        void onResultsClick(String item);
    }

    class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener {

        private TextView mTextView;

        public ViewHolder(View itemView) {
            super(itemView);
            mTextView = itemView.findViewById(R.id.tv_results_rv_item);
            mTextView.setOnClickListener(this);
        }

        public void bind(String item){
            mTextView.setText(item);
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
        holder.bind(mResultsList.get(position));
    }

    public void updateItems(ArrayList<String> items){
        mResultsList = items;
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
