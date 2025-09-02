#

import json

USE_JSON = True

btree = None
dumps = None
loads = None

if USE_JSON :
    ## Use json module for row serialization
    print ("Using json module")
    try :
        import btree
        dumps = lambda row_dict : bytes (json.dumps (row_dict).encode())
        loads = lambda row : json.loads (row.decode())
    except Exception as e :
        print (e)
else :
    ## Use umsgpack module for row serialization
    print ("Using umsgpack module")
    try :
        import umsgpack
        import btree
        dumps = lambda row_dict : umsgpack.dumps(row_dict)
        loads = lambda row : umsgpack.loads(row)
    except Exception as e :
        print (e)

simpledb_available = btree is not None

class SimpleDB :
    def __init__ (self,db_file_path,key_separator = ".",dump_separator="~",auto_commit=True) :
        if btree is None :
            print ("support module(s) missing")
            #raise ???
            return
        self.db_file = None
        try:
            self.db_file = open(db_file_path, "r+b")
        except OSError:
            self.db_file = open(db_file_path, "w+b")
        self.db = btree.open (self.db_file)
        self.key_separator = key_separator
        self.dump_separator = dump_separator
        self.auto_commit = auto_commit

    ## builds btree key from table_name and key
    def build_key (self,table_name,key="") -> bytes :
        pk = [table_name]
        if isinstance (key, list) :
            pk.extend (key)
        else :
            if len (key) > 0 :
                pk.append (key)
        #print ("build_key:", (self.key_separator.join (pk).encode ()))
        return bytes (self.key_separator.join (pk).encode ())
    ## writes/rewrites table row from row_dict
    def write_row (self,table_name,key,row_dict) :
        if isinstance (row_dict, dict) :
            row_dict ["key"] = key    # include key in row
        db_key = self.build_key(table_name, key)
        db_row = dumps(row_dict)
        #print ("w_r:", db_key, db_row)
        self.db [self.build_key(table_name, key)]=dumps(row_dict)
        if self.auto_commit :
            self.commit ()
    ## read row from table/key, returns None if not found
    def read_row (self,table_name,key) :
        #print ("read_row:", self.build_key (table_name, key))
        try :
            #print (loads (self.db [self.build_key (table_name, key)]))
            return loads (self.db [self.build_key (table_name, key)])
        except Exception :
            return None
    ## read next table indexed row, or first row if key is not provided
    def next_row (self,table_name,key = "") :
        row_ret = None             # Not found
        rows = self.get_table_rows (table_name, key, limit = 2)
        #print ("next_row", rows)
        for row in rows :
            if row["key"] != key :
                row_ret = row      # This is the next row
                break
        return row_ret
    ## Return True if this key is in table_name
    def row_exists (self,table_name,key) :
        return self.build_key (table_name, key) in self.db
    ## Delete row from table
    def delete_row (self,table_name,key) :
        if self.row_exists (table_name, key) :
            del (self.db [self.build_key (table_name, key)])
            if self.auto_commit :
                self.commit ()
    ## Returns list of keys in table
    def get_table_keys (self,table_name,start_key="",end_key="~~~~",limit=999999) :
        key_list = []
        for key in self.db.keys (self.build_key (table_name, start_key) ,
                                      self.build_key (table_name, end_key)) :
            #print ("gtk key:", key)
            key_elements = str (key).split (self.key_separator)
            key_list.append (key_elements [1])   # table key only
            if len (key_list) >= limit :
                break
        return key_list
    ## Returns list of rows in a table
    def get_table_rows (self,table_name,start_key="",end_key="~~~~",limit=999999) :
        rows = []
        for row in self.db.values (self.build_key (table_name, start_key) , # None) :
                                      self.build_key (table_name, end_key)) :
            #print ("gtr:", row)
            rows.append (loads (row))   # table key value
            if len (rows) >= limit :
                break
        
        #print ("gtr: rows", rows)
        return rows

    ## dump_all
    def dump_all (self, file_path = "db_dump.txt") :
        with open (file_path, "w") as dump_file :
            for key in self.db :
                row = self.db[key]
                key = str (key.decode ())
                if USE_JSON :
                    row = str (row.decode())
                else :
                    row = umsgpack.loads(row)
                    row = json.dumps (row)
                #print (f"dump: {key}{self.dump_separator}{row}")
                print (f"{key}{self.dump_separator}{row}", file=dump_file)
    ## load
    def load (self, file_path = "db_dump.txt") :
        print ("Loading:", file_path)
        with open (file_path, "r") as load_file :
            for line in load_file:
                key_row = (line.strip()).split (self.dump_separator)
                #print ("key_row:",key_row)
                key = bytes (key_row[0].encode ())
                row = bytes (key_row[1].encode ())
                print (f"load: key={key} row={row}")
                self.db [key] = row
                self.commit ()

    ## commit change (if autocommit is not set)
    def commit (self) :
        self.db.flush ()
    def close (self) :
        self.commit ()
        self.db.close ()
        self.db_file.close ()

# end SimpleDB  #

if __name__ == "__main__" :
    import os
    print (os.uname())
    db_file_name = "test.db"
    try :
        os.remove (db_file_name)
        print ("Removed:", db_file_name)
    except :
        pass
    my_db = SimpleDB  (db_file_name)
    if not simpledb_available :
        import sys
        print ("db failed to initialize")
        sys.exit ()

    #my_db.load ()
    #
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
    #
    #print ("good read:", my_db.read_row ("customer", "000100")) # Good key
    #print ("bad read:", my_db.read_row ("customer", "000199")) # bad key
    #print ("all keys:", my_db.get_table_keys ("customer"))
    #print ("rows:", my_db.get_table_rows ("customer", "000500", "990000"))
    row = my_db.next_row ("customer")
    #row = my_db.next_row ("customer", "000100")
    #print (row)
    while row is not None :
        #print ("next_row:", row)
        row = my_db.next_row ("customer", row["key"])
    #

    my_db.commit ()
    my_db.dump_all ()
    #my_db.load ()
    my_db.close ()

