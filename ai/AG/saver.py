import sqlite3


class Saver:

    def __init__(self, savefile):
        self.con = sqlite3.connect(savefile)
        self.cur = self.con.cursor()

        self.cur.execute("CREATE TABLE IF NOT EXISTS experiences(testfile, seed, step_simulated, generation, actions, score)")

    def save(self, testfile, seed, step_simulated, generation, actions, score):
        data = (testfile, seed, step_simulated, generation, actions, score)
        self.cur.execute("INSERT INTO experiences VALUES(?, ?, ?, ?, ?, ?)", data)
        self.con.commit()

    def get_best(self, testfile):
        res = self.cur.execute("""
            SELECT actions, score
            FROM experiences
            WHERE testfile LIKE ?
            ORDER BY score ASC
            LIMIT 1""", (f'%{testfile}', ))
        return res.fetchone()
