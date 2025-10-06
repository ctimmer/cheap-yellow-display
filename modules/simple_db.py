#
################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2025 Curt Timmerman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
################################################################################
#
## SimpleDB - Very simple relational database
#
# Notes:
#   o Uses btree module for DB engine.
#   o JSON is the default row storage format
#   o USE_JSON = False for umsgpack row storage format (more compact)
#
################################################################################

import time

## Required for load/dump
import json

## Default valules
KEY_SEPARATOR = "."
DUMP_SEPARATOR = "~"
DATE_FORMAT = "{:04d}-{:02d}-{:02d}"
TIME_FORMAT = "{:02d}:{:02d}:{:02d}"

USE_JSON = True
btree = None
dumps = None
loads = None

if USE_JSON :
    ## Use json module for row serialization
    print ("Using json module")
    try :
        import btree
        dumps = lambda row_data : bytes (json.dumps (row_data).encode())
        loads = lambda row : json.loads (row.decode())
    except Exception as e :
        print (e)
else :
    ## Use umsgpack module for row serialization
    print ("Using umsgpack module")
    try :
        import umsgpack
        import btree
        dumps = lambda row_data : umsgpack.dumps(row_data)
        loads = lambda row : umsgpack.loads(row)
    except Exception as e :
        print (e)

simpledb_available = btree is not None

##
class SimpleDB :
    def __init__ (self,db_file_path,key_separator=KEY_SEPARATOR,dump_separator=DUMP_SEPARATOR,auto_commit=True) :
        self.key_separator = key_separator
        self.key_low = ""
        self.key_high = "~~~~~"
        self.dump_separator = dump_separator
        self.auto_commit = auto_commit
        if btree is None :
            print ("support module(s) missing")
            #raise ???
            return
        ## OK, open file, btree DB
        self.db_file_path = db_file_path
        print (db_file_path)
        try:
            self.db_file = open(db_file_path, "r+b")
        except OSError:
            self.db_file = open(db_file_path, "w+b")
        self.db = btree.open (self.db_file)

    ## Return configuration
    def get_configuration (self) :
        return {
            "key_separator" : self.key_separator ,
            "dump_separator" : self.dump_separator ,
            "simpledb_available" : simpledb_available
            }

    ## builds btree key from table_name and key
    def build_key (self,table_name,key="") -> bytes :
        pk = [table_name]
        if key is None :
            pass
        elif isinstance (key, list) :
            for _, key_value in enumerate (key) :
                pk.append (str (key_value))
        else :
            pk.append (str (key))
        return bytes ((self.key_separator.join (pk)).encode ())
    def build_key_from_ids (self,table_name,pk_id=None,row_data=None) :
        key = None
        if pk_id is None :
            pass
        elif not isinstance (pk_id, list) :
            key = row_data [pk_id]
        else :
            key = []
            for _, key_id in enumerate (pk_id) :
                key.append (row_data [key_id])
        return self.build_key (table_name,key)

    ## rewrites table row from row_data
    def write_row (self,table_name,pk_id,row_data) :
        #print ("w_r:", table_name,pk)
        db_key = self.build_key_from_ids (table_name,pk_id,row_data)
        db_row = dumps(row_data)
        self.db [db_key] = db_row
        if self.auto_commit :
            self.commit ()
    ## rewrites updated table row from update_data
    def rewrite_row (self,table_name,key,update_data) :
        #print ("w_r:", table_name,pk)
        reply = None
        db_key = self.build_key (table_name, key)
        try :
            db_row = self.db [db_key]    # retrive current row
            db_row = loads (db_row)      # row to dict
            db_row.update (update_data)  # update row fields
            reply = json.dumps (db_row)  # save reply
            db_row = dumps (db_row)      # dict to internal format
            self.db [db_key] = db_row    # update DB row
        except Exception as e:
            print  (e)
            return None
        if self.auto_commit :
            self.commit ()
        return reply          # return updated row

    ## read row from table/key, returns None if not found
    def read_row (self,table_name,key) :
        #print ("read_row:", self.build_key (table_name, key))
        try :
            #print (loads (self.db [self.build_key (table_name, key)]))
            return loads (self.db [self.build_key (table_name, key)])
        except Exception :
            return None
    ## read row columns from table/key, returns None if not found
    def read_columns (self,table_name,key,column_list) :
        #print ("read_columns:", self.build_key (table_name, key), column_list)
        try :
            row = loads (self.db [self.build_key (table_name, key)])
            columns = {}
            # set valid valid column id test
            id_exists = None
            if isinstance (row, list) :
                id_exists = lambda col_id : col_id >= 0 and col_id < len (row)
            else :
                id_exists = lambda col_id : col_id in row
            for _, col_id in enumerate (column_list) :
                if id_exists (col_id) :
                    columns [col_id] = row [col_id]   # Valid column id
                else :
                    columns [col_id] = None           # Bad column id
            return columns
        except Exception as e :
            print (e)
            return None

    ## read first table indexed row, or first row if key is not provided
    def first_row (self,table_name,key = "") :
        row_ret = None             # Not found
        start_key = self.build_key (table_name, key)
        for db_key in self.db.keys (start_key, # None) :
                                    self.build_key (table_name, self.key_high)) :
            return loads (self.db [db_key])    # returns first key row
        return row_ret
    ## read next table indexed row, or first row if key is not provided
    def next_row (self,table_name,key = "") :
        row_ret = None             # Not found
        start_key = self.build_key (table_name, key)
        for db_key in self.db.keys (start_key, # None) :
                                    self.build_key (table_name, self.key_high)) :
            if db_key != start_key :
                return loads (self.db [db_key])
        return row_ret
    ## Return True if this key is in table_name
    def row_exists (self,table_name,key) :
        return self.build_key (table_name, key) in self.db
    ## Delete row from table
    def delete_row (self,table_name,key) :
        row_data = None
        delete_key = self.build_key (table_name, key)
        try :
            #print (loads (self.db [self.build_key (table_name, key)]))
            row_data = loads (self.db [delete_key])
            del (self.db [delete_key])
            if self.auto_commit :
                self.commit ()
        except Exception :
            pass
        return row_data

    ## Returns list of keys in table
    def get_table_keys (self,table_name,start_key=None,end_key=None,limit=999999) :
        key_list = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for key in self.db.keys (self.build_key (table_name, key_low) ,
                                      self.build_key (table_name, key_high)) :
            key = str (key.decode())
            #print ("gtk key:", key)
            key_elements = str (key).split (self.key_separator)
            key_list.append (key_elements [1])   # table key only
            if len (key_list) >= limit :
                break
        return key_list
    ## Returns list of rows in a table
    def get_table_rows (self,table_name,start_key=None,end_key=None,limit=999999) :
        rows = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for row in self.db.values (self.build_key (table_name, key_low) , # None) :
                                      self.build_key (table_name, key_high)) :
            rows.append (loads (row))   # table row
            if len (rows) >= limit :
                break
        return rows
    ## Returns list of rows in a table
    def get_table_items (self,table_name,start_key=None,end_key=None,limit=999999) :
        items = []
        key_low = start_key
        key_high = end_key
        if key_low is None :
            key_low = self.key_low
        if key_high is None :
            key_high = self.key_high
        #
        for item in self.db.items (self.build_key (table_name, key_low) , # None) :
                                      self.build_key (table_name, key_high)) :
            items.append ([str (item[0].decode()), loads (item[1])])   # table row
            if len (items) >= limit :
                break
        #print ("items:", items)
        return items

    ## dump_all
    def dump_all (self, file_path = None) :
        file_name = file_path
        if file_name is None :
            file_name = self.db_file_path + ".dump.txt"
        with open (file_name, "w") as dump_file :
            for key in self.db :
                row = self.db[key]
                key = str (key.decode ())
                ## Always dump row in json text format
                if USE_JSON :
                    row = str (row.decode())
                else :
                    row = umsgpack.loads(row)
                    row = json.dumps (row)
                #print (f"dump: {key}{self.dump_separator}{row}")
                #print (f"{key}{self.dump_separator}{row}", file=dump_file)
                dump_file.write (key + self.dump_separator + row + "\n")
    ## Build dump_all extract line (no database access)
    def dump_build_line (self,table_name,pk_id,row_data) :
        key = self.build_key_from_ids (table_name, pk_id, row_data).decode ()
        return key + self.dump_separator + json.dumps (row_data) + "\n"

    ## load - Load DB from dump_all file format
    def load (self, file_path = None) :
        file_name = file_path
        if file_name is None :
            file_name = self.db_file_path + ".dump.txt"
        print ("Loading:", file_name)
        with open (file_name, "r") as load_file :
            for line in load_file:
                key_row = (line.strip()).split (self.dump_separator)
                #print ("key_row:",key_row)
                key = bytes (key_row[0].encode ())
                if USE_JSON :
                    row = bytes (key_row[1].encode ())
                else :
                    row = json.loads (key_row[1])
                    row = dumps (row)
                print (f"load: key={key} row={row}")
                self.db [key] = row
                self.commit ()

    ## commit updates(s), if autocommit is not set
    def commit (self) :
        self.db.flush ()
    def close (self) :
        self.commit ()
        self.db.close ()
        self.db_file.close ()
        
    ## Utilities
    def get_date_time (self, epoch_seconds = None) :
        seconds = epoch_seconds
        if seconds is None :
            seconds = time.time ()
        local_time = time.localtime (seconds)
        return self.get_date (seconds) + " " + self.get_time (seconds)
    def get_date (self, epoch_seconds = None) :
        seconds = epoch_seconds
        if seconds is None :
            seconds = time.time ()
        local_time = time.localtime (seconds)
        return DATE_FORMAT.format (local_time[0],local_time[1],local_time[2])
    def get_time (self, epoch_seconds = None) :
        seconds = epoch_seconds
        if seconds is None :
            seconds = time.time ()
        local_time = time.localtime (seconds)
        return TIME_FORMAT.format (local_time[3],local_time[4],local_time[5])

# end SimpleDB  #

def main () :
    import os
    #print (os.uname())
    db_file_name = "btree_test.db"
    try :
        os.remove (db_file_name)
        print ("Removed:", db_file_name)
    except :
        pass
    my_db = SimpleDB (db_file_name)
    print ("build_row:",my_db.dump_build_line ("customer",
                                                "customer_number" ,
                                                {"customer_number" : "000100" ,
                                                    "name":"Curt" ,
                                                    "dob":19560606 ,
                                                    "occupation":"retired"}))
    if not simpledb_available :
        import sys
        print ("db failed to initialize")
        sys.exit ()

    print (my_db.get_date_time ())
    print (my_db.get_date ())
    print (my_db.get_time ())
    #my_db.load ()
    #
    my_db.write_row ("customer", "customer_number" ,  {"customer_number" : "000100" ,
                                                        "name":"Curt" ,
                                                        "dob":19560606 ,
                                                        "occupation":"retired"})
    print ("rewrite_row:" ,
        my_db.rewrite_row ("customer", "000100" , {"location" : "Alaska"}))
    print ("read_columns:" ,
        my_db.read_columns ("customer", "000100" , ["name","location","bad_id"]))
    my_db.write_row ("customer", "customer_number", {"customer_number" : "000500" ,
                                            "name":"Moe" ,
                                            "dob":19200101 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "010000" ,
                                            "name":"Larry" ,
                                            "dob":19210202 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "001000" ,
                                            "name":"Curly" ,
                                            "dob":19250303 ,
                                            "occupation":"Three stooges"})
    my_db.write_row ("customer", "customer_number", {"customer_number" : "999999" ,
                                            "name":"Delete test" ,
                                            "dob":20000101 ,
                                            "occupation":"doesnt matter"})
    my_db.write_row ("invoice",
                    "invoice_number" ,
                    {"invoice_number" : "090001" ,
                    "customer_number" : "001000"})
    my_db.write_row ("invoice_line",
                    ["invoice_number", "line_number"] ,
                    {"invoice_number" : "090001" ,
                    "line_number" : "0001" ,
                    "sku" : "Snake Oil" ,
                    "price" : "100.00"})
    my_db.write_row ("invoice_line",
                    ["invoice_number", "line_number"] ,
                    {"invoice_number" : "090001" ,
                    "line_number" : "0002" ,
                    "sku" : "Aspirin" ,
                    "price" : "12.00"})
    my_db.write_row ("log",
                    0 ,
                    ["20250903122010","Error","Log error"])
    my_db.write_row ("log",
                    0 ,
                    ["20250904141020","Warning", "Log warning"])

    print ("read_columns:" ,
        my_db.read_columns ("log", "20250904141020" , [0,3]))
    #
    print ("good read:", my_db.read_row ("customer", "000100")) # Good key
    print ("bad read:", my_db.read_row ("customer", "000199")) # bad key
    print ("all keys:", my_db.get_table_keys ("customer"))
    print ("rows:", my_db.get_table_rows ("customer", "000500", "990000"))
    if my_db.row_exists ("customer", "999999") :
        print ("Delete row:", my_db.delete_row ("customer", "999999"))
        if my_db.row_exists ("customer", "999999") :
            print ("customer 999999 was not delete")
        else :
            print ("customer 999999 delete success")
    else :
        print ("Customer: 999999 missing")
    #
    #print (my_db.get_table_items ("customer"))

    row = my_db.first_row ("customer")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("customer", row["customer_number"])
    #
    row = my_db.first_row ("log")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("log", row[0])
    #
    row = my_db.first_row ("error_table")
    while row is not None :
        print ("row:", row)
        row = my_db.next_row ("log", row[0])
    #
    my_db.dump_all ()
    my_db.close ()

#----------------------------------------------------
if __name__ == "__main__" :
    main ()
