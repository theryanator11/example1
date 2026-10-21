import java.awt.Color;
import java.awt.Graphics2D;

public class Projectile {
    public int x, y;
    public int speed = 10;
    public boolean active = true;

    public Projectile(int startX, int startY) {
        this.x = startX;
        this.y = startY;
    }

    public void update() {
        y -= speed;
        if (y < 0) active = false; 
    }

    public void draw(Graphics2D g2) {
        g2.setColor(Color.YELLOW);
        g2.fillRect(x, y, 4, 15);
    }
}