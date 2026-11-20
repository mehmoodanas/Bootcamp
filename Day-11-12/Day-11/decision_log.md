# Decision Log: Local RAG Pipeline

## Machine
- **Hardware:** 
  - Laptop: HP Elitebook 840 G7
  - CPU: intel core i5-10210U(4 cores, 8 threads)
  - RAM: 16 GB
  - GPU: no dedicated GPU
  - OS: windows 11 pro
  - Ollama 0.40.16 installed on windows natively
- **`ollama ps` with my main model loaded:**
```
NAME                 ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL              
qwen3.5:4b-q4_K_M    d8b0f5e9760c    3.4 GB    100% CPU     8192       llamacpp    4 minutes from now    
```

## Model Selection
- **Chosen LLM:** qwen3.5:4b-q4_K_M
- **Thinking:** I turned off thinking. There are two reasons which i saw. First one is this model thinks first and then answers and thinkingand answer both uses the same token limit and if thinking will finish the token limit then the answer will be empty. So to be safe from that problem i turned off thinking and the Second reason is that QWen model in the CPU is already slow, if i run with thinking tuned off. So with the thinking the model will generate results very slowly.
- **Why:** 
    - Reference: I tested 3 models and saved results in the **benchmark_results.json** file in which i gave 7 small tasks to all 3 models and then i gave score to each of them to compare and choose one model from them
    1. qwen3.5:4b   -> 4.71 
    2. qwen3.5:2b   -> 3.86 
    3. llama3.2:3b  -> 4.43
    so between these 3 models qwen model with 4b gave best accuracy than other models and thats why i chose it.

    - Comparison: i compared 3 models on the basis of **7 different types of tasks** like fact question , mathematically, code etc. And **quality** in which i gave score to each tasks between 1-5. Then checked the **speed** of each model and calculated the average tokens per second according to this 2b is faster but acccuracy wise worst. 
    
    - Why i choose this? I choose qwen model with 4b because it is more accurate.
        I tested in several ways all of them and yes 4b model is little bit slower but acceptable and 2b model gives wrong answers if it is not available in the text but still it tries to answer something instead of saying no confidently and by doing chunks into 512 and top_k5 4b model gave 14/18 and llama model gave 12/18 correact answers **(pipeline_outputs_4b_c512_k5.json, pipeline_outputs_llama3.2_3b.json)** and then i tried to improved them and then i changed the chinking size into 1000 and top_k=8 and it improved the result into 4b=17/18, llama= 14/18 **(pipeline_outputs_4b_c1000_k8.json, pipeline_outputs_llama_c1000_k8.json)**. So by watching all this we all can see that qwen 4b model is bestest in all of them

- **What I considered but rejected:** 
    1. Qwen3.5:2b: It is good in speed but the reason of rejecting is that it invets answers by itself
    2. lama3.2:3b: This model was also good but the only reason of rejecting is that it gave more wrong answers than qwen3.5:4b
    3. qwen3.5:9b: i didnt try this model because it is too slow for my laptop. Even 4b model was very slow and my laptop hangged for a little bit time.

## Embedding Model
- **Chosen:** i chose nomic-embed-text model with vector dimension of 768 numbers. which helps to understand the meaning of text using this numbers.
- **Why:** I compared with mxbai-embed-large. And both worked well in right document for all questions and nomic is faster than other model. Both found the right document for 16/16 questions. Both sources were found by mxbai in 16/16 and by nomic in 15/16. Average time per question: nomic 50 ms, mxbai 134 ms **embedding_comparison.json**.
- Tradeoff: mxbai is slower and bigger than nomic but it finds document a little better than nomic.

## Parsing
- **Extractor:** For extractor i used pypdf library to read the PDFs. This library read the pdf page by page, one page at a time. And there are 2 modes 1. normal mode, 2. Layout mode. I checked both which works best and then used the good one which is the layout mode. I tested it on the revenue table of quarterly_report_q1_2026.pdf, page 2, with parse_check.py.
    1. Normal mode: I used the table of the revenue and wanted to come out properly but it came out broken. every word or number in the new line.
        ```
        Quarterly Revenue
        EUR
        4.8M
        ```
    2. Layout mode: This mode is better because it didnt break the table. It worked well and each row of the table stayed in one line.
        
        ```
        ProjectHub   EUR 3.36M   70%   +26%
        ```


    As we can see here the difference clearly which one is good and which one we need to use.
## Chunking Strategy
- **Chunk size:** 1000 characters 
- **Overlap:** 80 characters
- **Why:** yes i did experiment first with the default given chunk size of 512 characters and 50 characters overlap and it gave results and gave 334 chunks and gave 14 answers correct out of 18 **pipeline_outputs_4b_c512_k5.json**. Then to increase its correctness i tried to change the chunk size and overlap also and i changed it into 1000 characters and overlap 80 characters. When i used 512 some are failed because of small chunks i think so. So i tried to make the chunk bigger so that it will get information better and improve the results and it worked. When i used 1000 character and 80 overlap characters it divided the chunks into 188 chunks. It failed one answer only and gave 17/18 correct **pipeline_outputs_4b_c1000_k8.json**. It fixed the question number 7, 10, 11, 16 but failed in the 15, which was correct before with 512.

## Retrieval Configuration
- **Top-K:** top_k=5
- **Context window:** Mine context window is 8192 tokens from ollama ps. In which i used top_k 5, with this each question sent from 916 to 1545 prompt tokens **pipeline_outputs.json**. Nothing was cut off because it is very less than our context window so it is good.
- **Why:** Yes i tried 3 times by changing chunking size of chaaracters and top_k and then chunking size remained same and i changed top_k 2 times.
First time i did 512 character chunks and top_k 5 and it gave 14 correct **pipeline_outputs_4b_c512_k5.json** only because some of the chunks are missing and then i tried top_k 8 with 1000 character chunks and it gave me 17 correct **pipeline_outputs_4b_c1000_k8.json** because of greater chunk size but it was slower and then i tried with same chunk size and top_k 5 and it gave the same result 17 correct **pipeline_outputs_4b_c1000_k5.json** but it is much faster than with top_k 8. So i chose with top_k=5 because it is faster and accurate also.

## Observations
- **What worked well:** some wuestions passed easily because they answered correct. Easy questions from question 1-6 are all correct even it gave correct page number from the required pdf name. And question 9 and 12 also worked with table questions and it gave correct answers which means layout parsing worked properly. And from the questions of conflict 13, 14 and 16. It answered both sources because of conflict. And the questions 17 and 18 they didnt invent anything and refused.
- **What failed:** Everything was going good but at question 15 only it failed **pipeline_outputs.json**. From the example the 79 euro is a monthly amount and answer showed it is annual price while 66 is the annual price. And even the passed answers also gave some smll mistakes like in question 10 the professional downtime was 43 but it showed 21 and in the 13th it should show 4th day remote rule but it showed it as a proposal. And in the first run when i used 512 chunk size of characters then question 7,10,11 failed because the right chunk was missing.
- **Traps I hit:** 
    - The context window was 4096 before and i changed it into 8192 but still it showed 4096. It was running before i think so i restarted ollama again and it fixed the conext window.
    - When i tried to use chroma Dbthen the smart controll app of laptop blockef file to use grpcio and then i tried to download the old version and i ran and it worked.
    - I used layout mode because when i used normal it breaks the tables.
- **Local vs cloud expectations:** 
   As one model was local and one was cloud model. And local model is on my laptop which automatically means my laptop will be slower than the cloud model and also i expected when i used chunk size 512 that it will work properly but because of some answers are lengthier and the right side of the chunk was missing so it broke the table and other answers.

## If I Had More Time / Better Hardware
- [What would you change?]
If i had more time i would like to try other embedding models and chunk size and different values of top_k and also the security features and then analyze it how it will work and what is best. Sample data is small but i think so using different techniques will still help to analyze the different features and make the summary which one is better to use in both local and cloud.
And no doubt i would like to try it on the better hardware. Gpu is strong and much faster.
And i would like to increase the sample data of test questions including every types to analyze more correctly and repeated runs
