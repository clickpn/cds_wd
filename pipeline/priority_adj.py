import pandas as pd
import os

high_kws_lst = ['black tail', 'mule', 'roe deer', 'grey fox', 'ivory', 'geese']

low_kws_lst = ['polished handicraft abalone', 'blacktail deer', 'quail',
'duck farm raised','bobcat','hybrid wolf','deer hide','white tail deer',
'red fox','sting ray']

def adjust_priority(data):
    data['old_scores'] = data['rel_scores']
    for index, row in data.iterrows():
        score = row['old_scores']
        if score > 0.75 and score <= 1:
            if any(word in row for word in high_kws_lst):
                row['rel_scores'] = 1
            else:
                row['rel_scores'] = score
        elif score <= 0.75 and score > 0.5:
            if any(word in row for word in low_kws_lst):
                row['rel_scores'] = 0.6
            else:
                row['rel_scores'] = score
        else:
            row['rel_scores'] = score
    return data

def main():
    input_path = './csv_file'
    for file in os.listdir(input_path):
        df = pd.read_csv(input_path + '/' + file)
        adj_df = adjust_priority(df)
        adj_df.to_csv(input_path + '/' + file)

if __name__ == '__main__':
    main()
