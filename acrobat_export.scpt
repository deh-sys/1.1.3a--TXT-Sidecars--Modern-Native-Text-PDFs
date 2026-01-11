on run argv
    set pdfPath to item 1 of argv
    set outputPath to item 2 of argv

    -- Escape backslashes and single quotes for JavaScript string
    set jsCode to "var f = '" & my jsEscapePath(outputPath) & "';" & return & "this.saveAs(f, 'com.adobe.acrobat.docx');"

    -- Open PDF in background (no focus steal)
    do shell script "open -g -a 'Adobe Acrobat' " & quoted form of pdfPath

    tell application "Adobe Acrobat"
        -- Wait for document to load
        repeat until (count of documents) > 0
            delay 0.2
        end repeat

        tell active doc
            -- Blocks until JavaScript saveAs completes (JS is default)
            do script jsCode
            close saving no
        end tell

        -- Wait for document to fully close before returning
        repeat while (count of documents) > 0
            delay 0.3
        end repeat
        delay 3
    end tell
end run

on jsEscapePath(p)
    set AppleScript's text item delimiters to "\\"
    set theItems to every text item of p
    set AppleScript's text item delimiters to "\\\\"
    set p to theItems as string
    set AppleScript's text item delimiters to ""

    set AppleScript's text item delimiters to "'"
    set theItems to every text item of p
    set AppleScript's text item delimiters to "\\'"
    return theItems as string
end jsEscapePath
