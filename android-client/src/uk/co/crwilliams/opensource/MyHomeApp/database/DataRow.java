package uk.co.crwilliams.opensource.MyHomeApp.database;

public class DataRow {

    private final String room;
    private final String value;
    private final String type;
    private final int time;

    public DataRow(String room, String value, String type, int time) {
        this.room = room;
        this.value = value;
        this.type = type;
        this.time = time;
    }

    public String getRoom() {
        return this.room;
    }

    public String getValue() {
        return this.value;
    }

    public String getType() {
        return this.type;
    }

    public int getTime() {
        return this.time;
    }
}
