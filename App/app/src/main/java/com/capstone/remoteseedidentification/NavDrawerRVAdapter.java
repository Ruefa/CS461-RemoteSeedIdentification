package com.capstone.remoteseedidentification;

import android.content.Context;
import android.support.v7.widget.RecyclerView;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.util.ArrayList;

/**
 * Created by Alex on 3/14/2018.
 */

public class NavDrawerRVAdapter extends RecyclerView.Adapter <NavDrawerRVAdapter.ViewHolder> {

    private ArrayList<String> mNDItems;
    private Context mContext;
    private onNavDrawerItemClickListener mNavDrawerClickListener;

    public interface onNavDrawerItemClickListener{
        void onNavDrawerItemClick(String item);
    }

    class ViewHolder extends RecyclerView.ViewHolder implements View.OnClickListener {

        private TextView mOptionTV;

        public ViewHolder(View itemView) {
            super(itemView);
            mOptionTV = itemView.findViewById(R.id.nav_drawer_item);
            mOptionTV.setOnClickListener(this);
        }

        public void bind(String item){
            mOptionTV.setText(item);
        }

        @Override
        public void onClick(View v){
            String item = mNDItems.get(getAdapterPosition());
            mNavDrawerClickListener.onNavDrawerItemClick(item);
        }
    }

    public NavDrawerRVAdapter(Context context, onNavDrawerItemClickListener clickListener){
        mContext = context;
        mNavDrawerClickListener = clickListener;
    }

    public void updateItems(ArrayList<String> items){
        mNDItems = items;
        notifyDataSetChanged();
    }

    @Override
    public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(parent.getContext());
        View itemView = inflater.inflate(R.layout.nav_drawer_rv_layout, parent, false);
        return new ViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(ViewHolder holder, int position) {
        holder.bind(mNDItems.get(position));
    }


    @Override
    public int getItemCount() {
        if (mNDItems != null){
            return mNDItems.size();
        }else{
            return 0;
        }
    }
}
