import java.awt.Color;
import java.awt.Graphics2D;

public class EnemyLaser {
    public double x, y;
    public double dx, dy; 
    public boolean active = true;

    public EnemyLaser(double startX, double startY, double dx, double dy) {
        this.x = startX;
        this.y = startY;
        this.dx = dx;
        this.dy = dy;
    }

    public void update(GamePanel gp) {
        x += dx;
        y += dy;
        
        if (y > gp.screenHeight + 20 || y < -20 || x < -20 || x > gp.screenWidth + 20) {
            active = false;
        }
    }

    public void draw(Graphics2D g2) {
        g2.setColor(Color.WHITE);
        g2.fillOval((int)x - 4, (int)y - 4, 8, 8);
        g2.setColor(Color.RED);
        g2.drawOval((int)x - 4, (int)y - 4, 8, 8);
    }
}