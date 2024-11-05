#!/usr/bin/python3
'''
The goal of this script is to compute statistical information regarding PC members bidding
for papers in one conference.  The code is based on Mathias Payer's code at
 https://github.com/HexHive/inquisitor/blob/main/check_bidding.py. 
'''

import csv
import sys

class Conference:
    def __init__(self, year, name):
        self.year = year
        self.name = name
        self.author_names = {}    # map each author email to full name
        self.num_papers = {}     # map each author email to number of submissions
        self.paper_authors = {}  # map each paper id to a list of author emails
        self.reviewers = {}      # map each reviewer email to Reviewer object
        
    def add_one_cycle(self, cycle, authors_csv_filename, allpref_csv_filename):
        # read from the csv file containing all authors
        with open(authors_csv_filename, 'r', encoding="utf8") as f:
            papers_csv = csv.reader(f)
            paper_id = 0
            for row in papers_csv:
                if row[0] == 'paper':
                    # header line; skip.  The assertion below is our assumption; but one coud use different field names
                    # assert(row[1] == 'title' and row[2] == 'first' and row[3] == 'last' and row[4] == 'email')
                    continue
                paper_id = cycle+row[0]
                first_name, last_name, email = row[2], row[3], row[4]
                
               
                # Add author full information when seeing the author for the first time
                author_full_name = '{} {}'.format(first_name, last_name)
                if email == "":
                    #print(author_full)
                    continue

                if not email in self.author_names:
                    self.author_names[email] = author_full_name
                
                # Add author email to the list associated with the paper_id
                if paper_id in self.paper_authors:
                    self.paper_authors[paper_id].append(email)
                else:
                    self.paper_authors[paper_id] = [email]
                
                # Count number of submissions by each author 
                if email in self.num_papers:
                    self.num_papers[email] += 1
                else:
                    self.num_papers[email] = 1

        # read from the csv file containing all preferences
        with open(allpref_csv_filename, 'r', encoding="utf8") as f:
            allprefs_csv = csv.reader(f)
            for row in allprefs_csv:
                if row[0] == 'paper':
                    # head line, skip. We assume the following data format
                    # assert(row[2] == 'given_name' and row[3] == 'family_name' and row[4] == 'email' and row[6] == 'preference' and row[7] == 'topic_score')
                    continue
                paper_id = cycle+row[0]
                first_name, last_name, email = row[2], row[3], row[4]
                if not email in self.reviewers:
                    self.reviewers[email] = self.Reviewer(self, first_name, last_name, email)
                preference = int(row[6]) if row[6] != '' else 0
                topic_score = int(row[7]) if row[7] != '' else 0
                self.reviewers[email].add_bid(self.paper_authors[paper_id], preference, topic_score)
                
    def gen_report(self):
        bai_table = []
        for reviewer in self.reviewers:
            self.reviewers[reviewer].report(bai_table)
        bai_table.sort(reverse = True)
        return bai_table
        
    class Reviewer:
        def __init__(self, conf, first_name, last_name, email):
            self.conf = conf
            self.email = email
            self.full_name =  '{} {}'.format(first_name, last_name)
            self.pos_bid_num = 0
            self.pos_pref_sum = 0
            self.bid_per_author = {}    # map each author email to (count, sum_pref)
            
        def add_bid(self, paper_authors, preference, topic_score):
            if preference >= 5:         # significant positive bids
                self.pos_bid_num += 1
                self.pos_pref_sum += preference
                for author in paper_authors:
                    if author in self.bid_per_author:
                        self.bid_per_author[author][0] += 1
                        self.bid_per_author[author][1] += preference
                    else:
                        self.bid_per_author[author] = [1, preference]
        
        def report(self, bai_table):
            for author in self.bid_per_author:
                [num, pref] = self.bid_per_author[author]
                bai = pref / self.pos_pref_sum              # what fraction of reviewer's bid go to the author
                frac = num / self.conf.num_papers[author]    # what fraction of the authors' papers is bid
                if  num >= 3 or (num>=2 and frac>=0.5):
                    bai_table.append([num, bai, self.pos_bid_num, self.pos_pref_sum, self.email, self.full_name, author, self.conf.author_names[author], self.conf.num_papers[author]])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Run the script with: python3 {} output_file_name'.format(sys.argv[0]))
        exit(1)
    conference = Conference(2023, "CCS")
    files = [ ["a", "data\\ccs2023a-authors.csv", "data\\ccs2023a-allprefs.csv"],
              ["b", "data\\ccs2023b-authors.csv", "data\\ccs2023b-allprefs.csv"], ]

    '''
    conference = Conference(2024, "CCS")
    files = [ ["a", "data\\ccs2024a-authors.csv", "data\\ccs2024a-allprefs.csv"],
              ["b", "data\\ccs2024b-authors.csv", "data\\ccs2024b-allprefs.csv"], ]
    '''
    
    for [cycle, paper_file, pref_file] in files:
        conference.add_one_cycle(cycle, paper_file, pref_file)

    bai_table = conference.gen_report()

    with open(sys.argv[1], 'w', encoding="utf8", newline='') as file:
        writer = csv.writer(file)
        writer.writerows(bai_table)
