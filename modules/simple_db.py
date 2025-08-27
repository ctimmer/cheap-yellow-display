#

btree = None

try :
    import btree
    import json
except Exception as e :
    print (e)

simpledb_available = btree is not None

class SimpleDB :
    def __init__ (self ,
                  db_file_path ,
                  key_separator = "." ,
                  auto_commit = True) :
        if btree is None :
            print ("btree module is missing")
            #raise ???
            return
        try:
            db_file = open(db_file_path, "r+b")
        except OSError:
            db_file = open(db_file_path, "w+b")
        self.db = btree.open (db_file)
        self.key_separator = key_separator
        self.auto_commit = auto_commit
    
    def build_key (self ,
                    table_name ,
                    key) :
        return bytes ((table_name + self.key_separator + key).encode ())

    def write_row (self ,
                    table_name ,
                    key ,
                    row_dict) :
        row_dict ["key"] = key    # include key in row
        self.db [self.build_key (table_name, key)] = bytes (json.dumps (row_dict).encode())
        if self.auto_commit :
            self.db.flush ()

    def read_row (self ,
                    table_name ,
                    key) :
        try :
            return json.loads (self.db [self.build_key (table_name, key)])
        except Exception :
            return None
    def next_row (self ,
                    table_name ,
                    key = "") :
        row_ret = None
        rows = self.get_table_rows (table_name, key, limit = 2)
        #print ("next_row", rows)
        for row in rows :
            if row["key"] != key :
                row_ret = row
                break
        return row_ret

    def row_exists (self ,
                    table_name ,
                    key) :
        return self.build_key (table_name, key) in self.db

    def delete_row (self ,
                    table_name ,
                    key) :
        del (self.db [self.build_key (table_name, key)])
    
    def get_table_keys (self,
                        table_name ,
                        start_key = "" ,
                        end_key = str (0xff) ,
                        limit = 999999) :
        key_list = []
        for key in my_db.db.keys (self.build_key (table_name, start_key) ,
                                      self.build_key (table_name, end_key)) :
            key_elements = str (key).split (self.key_separator)
            key_list.append (key_elements [1])   # table key only
            if len (key_list) >= limit :
                break
        return key_list
    def get_table_rows (self,
                        table_name ,
                        start_key = "" ,
                        end_key = str (0xff) ,
                        limit = 999999) :
        rows = []
        for row in my_db.db.values (self.build_key (table_name, start_key) ,
                                      self.build_key (table_name, end_key)) :
            rows.append (json.loads (row.decode()))   # table key value
            if len (rows) >= limit :
                break
        return rows

    def commit (self) :
        self.db.flush ()
    def close (self) :
        self.commit ()
        self.db.close ()

# end SimpleDB  #

if __name__ == "__main__" :
    my_db = SimpleDB  ("test.db")
    if not simpledb_available :
        import sys
        print ("db failed to initialize")
        sys.exit ()
    my_db.write_row ("customer", "000100", {"name":"Curt" ,
                                            "dob":19560606 ,
                                            "occupation":"retired"})
    my_db.write_row ("customer", "000500", {"name":"Moe" ,
                                            "dob":19200101 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "010000", {"name":"Larry" ,
                                            "dob":19210202 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "001000", {"name":"Curly" ,
                                            "dob":19250303 ,
                                            "occupation":"Three stooges"})
    print ("read:", my_db.read_row ("customer", "000100")) # Good key
    print ("read:", my_db.read_row ("customer", "000199")) # bad key
    print ("all keys:", my_db.get_table_keys ("customer"))
    print ("rows:", my_db.get_table_rows ("customer", "000500", "990000"))
    row = my_db.next_row ("customer", "000500")
    while row is not None :
        print ("next:", row)
        row = my_db.next_row ("customer", row["key"])
    #
    my_db.commit ()
    my_db.close ()

