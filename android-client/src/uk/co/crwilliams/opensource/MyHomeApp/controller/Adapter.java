package uk.co.crwilliams.opensource.MyHomeApp.controller;

import android.content.Context;
import android.graphics.Color;
import android.graphics.PorterDuff;
import android.text.format.DateFormat;
import android.view.*;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.TextView;
import uk.co.crwilliams.opensource.MyHomeApp.Constants;
import uk.co.crwilliams.opensource.MyHomeApp.R;
import uk.co.crwilliams.opensource.MyHomeApp.database.DataRow;

import java.util.Date;
import java.util.List;

public class Adapter extends ArrayAdapter<DataRow> {
    private final Display display;

    public Adapter(Context context, List<DataRow> objects) {
        super(context, R.layout.row, objects);
        display = ((WindowManager)getContext().getSystemService(Context.WINDOW_SERVICE)).getDefaultDisplay();
    }

    @Override
    public View getView(int position, View convertView, ViewGroup parent) {
        if(convertView == null) {
            convertView = View.inflate(getContext(), R.layout.row, null);
        }

        DataRow row = getItem(position);

        ((TextView)convertView.findViewById(R.id.text_room_name)).setText(row.getRoom());

        setVisibility(convertView, row);

        Date date = new Date(1000L * row.getTime());
        String timestamp = DateFormat.getTimeFormat(getContext()).format(date) + ' ' +
                           DateFormat.getDateFormat(getContext()).format(date);

        ((TextView)convertView.findViewById(R.id.text_update_time)).setText(timestamp);

        setColor(
                (Button)convertView.findViewById(R.id.button_on),
                (Button)convertView.findViewById(R.id.button_off),
                row.getValue());
        setColorLowMediumHigh(
                (Button)convertView.findViewById(R.id.button_low),
                (Button)convertView.findViewById(R.id.button_medium),
                (Button)convertView.findViewById(R.id.button_high),
                row.getValue());

        return convertView;
    }

    private void setVisibility(View convertView, DataRow row) {
        if("".equals(row.getType())) {
            convertView.findViewById(R.id.button_on).setClickable(false);
            convertView.findViewById(R.id.button_off).setVisibility(View.INVISIBLE);
        } else {
            convertView.findViewById(R.id.button_on).setClickable(true);
            convertView.findViewById(R.id.button_off).setVisibility(View.VISIBLE);
        }

        int visibility = View.INVISIBLE;
        if(display.getRotation() == Surface.ROTATION_0 || display.getRotation() == Surface.ROTATION_180) {
            visibility = View.GONE;
        } else if("SwitchMultilevel".equals(row.getType())) {
            visibility = View.VISIBLE;
        }
        convertView.findViewById(R.id.button_low).setVisibility(visibility);
        convertView.findViewById(R.id.button_medium).setVisibility(visibility);
        convertView.findViewById(R.id.button_high).setVisibility(visibility);
    }

    private void setColor(Button buttonOn, Button buttonOff, String value) {
        if ("0".equals(value) || "False".equals(value)) {
            buttonOn.getBackground().clearColorFilter();
            buttonOff.getBackground().setColorFilter(Color.RED, PorterDuff.Mode.MULTIPLY);
        } else if("?".equals(value)) {
            buttonOn.getBackground().clearColorFilter();
            buttonOff.getBackground().clearColorFilter();
        } else {
            buttonOn.getBackground().setColorFilter(Color.GREEN, PorterDuff.Mode.MULTIPLY);
            buttonOff.getBackground().clearColorFilter();
        }
    }

    private void setColorLowMediumHigh(Button buttonLow, Button buttonMedium, Button buttonHigh, String value) {
        buttonLow.getBackground().clearColorFilter();
        buttonMedium.getBackground().clearColorFilter();
        buttonHigh.getBackground().clearColorFilter();
        if (Constants.LEVEL_LOW.equals(value)) {
            buttonLow.getBackground().setColorFilter(Color.BLUE, PorterDuff.Mode.MULTIPLY);
        } else if(Constants.LEVEL_MEDIUM.equals(value)) {
            buttonMedium.getBackground().setColorFilter(Color.BLUE, PorterDuff.Mode.MULTIPLY);
        } else if(Constants.LEVEL_HIGH.equals(value)) {
            buttonHigh.getBackground().setColorFilter(Color.BLUE, PorterDuff.Mode.MULTIPLY);
        }
    }
}
