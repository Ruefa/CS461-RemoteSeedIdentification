package com.capstone.remoteseedidentification;

import android.content.Context;
import android.support.v7.widget.RecyclerView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.util.ArrayList;

/**
 * Created by Alex on 3/14/2018.
 */

public class NavDrawerRVAdapter extends RecyclerView.Adapter <NavDrawerRVAdapter.ViewHolder> {

    ArrayList<String> mNDItems;
    Context mContext;

    class ViewHolder extends RecyclerView.ViewHolder {

        private TextView mOptionTV;

        public ViewHolder(View itemView) {
            super(itemView);
            mOptionTV = itemView.findViewById(R.id.nav_drawer_item);
        }

        public void bind(String item){
            mOptionTV.setText(item);
        }
    }

    public NavDrawerRVAdapter(Context context){
        mContext = context;
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
