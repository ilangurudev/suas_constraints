library(tidyverse)

str_problem <- read_file("sample3.txt") %>% 
  str_split("\n") %>% pluck(1)

df_problem <- 
  tibble(line = str_problem) %>% 
  mutate(is_pilot_line = line %>% str_detect("P "),
         is_mission_line = line %>% str_detect("M "))

df_problem %>% 
  filter(is_pilot_line)

df_problem %>% 
  filter(is_mission_line)

df_results <- read_delim("results3.txt", col_names = c("mission", "model", "pilot", "preference"), delim = " ")


df_results %>% 
  count(model, pilot, preference)
