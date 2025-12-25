main :: IO ()
main = do
    putStrLn "Enter your address:"
    addr <- getLine
    putStrLn ("Your address is: " ++ addr)
