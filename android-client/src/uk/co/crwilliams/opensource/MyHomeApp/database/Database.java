package uk.co.crwilliams.opensource.MyHomeApp.database;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.database.sqlite.SQLiteStatement;

import java.util.ArrayList;

public class Database extends SQLiteOpenHelper {
    private static final String DATABASE_NAME = "MyHomeData";
    private static final int DATABASE_VERSION = 1;
    private static final String ROOM = "room";
    private static final String VALUE = "value";
    private static final String TIME = "time";
    private static final String TYPE = "type";
    private static final String DATA_TABLE_NAME = "data";
    private static final String DATA_TABLE_CREATE =
            "CREATE TABLE " + DATA_TABLE_NAME + " (" +
                    ROOM + " TEXT PRIMARY KEY, " +
                    VALUE + " TEXT, " +
                    TYPE + " TEXT, " +
                    TIME + " DATETIME);";

    public Database(Context context) {
        super(context, DATABASE_NAME, null, DATABASE_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL(DATA_TABLE_CREATE);
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
    }

    public void update(String room, String value, String type, int time) {
        SQLiteStatement stmt;

        if(type == null) {
            type = "";
        }
        /*
        this.getWritableDatabase().compileStatement(
                "INSERT OR IGNORE INTO data (room, value) VALUES ('tree', '?')").execute();
        this.getWritableDatabase().compileStatement(
                "INSERT OR IGNORE INTO data (room, value) VALUES ('xmas', '?')").execute();
        this.getWritableDatabase().compileStatement(
                "INSERT OR IGNORE INTO data (room, value) VALUES ('lamp', '?')").execute();
        */

        stmt = getWritableDatabase().compileStatement(
                "INSERT OR IGNORE INTO data (room, value, type, time) VALUES (?, ?, ?, ?)");
        stmt.bindString(1, room);
        stmt.bindString(2, value);
        stmt.bindString(3, type);
        stmt.bindLong(4, time);
        stmt.execute();

        stmt = getWritableDatabase().compileStatement(
                "UPDATE data SET value = ?, type = ?, time = ? WHERE room = ?");
        stmt.bindString(1, value);
        stmt.bindString(2, type);
        stmt.bindLong(3, time);
        stmt.bindString(4, room);
        stmt.execute();
    }

    public void updateData(ArrayList<DataRow> rows) {
        rows.clear();

        String[] columns = {"room", "value", "type", "time"};
        Cursor c = getReadableDatabase().query("data", columns, null, null, null, null, "room");

        if (c.moveToFirst()) {
            do {
                rows.add(new DataRow(c.getString(0), c.getString(1), c.getString(2), c.getInt(3)));
            } while (c.moveToNext());
        }
    }
}
