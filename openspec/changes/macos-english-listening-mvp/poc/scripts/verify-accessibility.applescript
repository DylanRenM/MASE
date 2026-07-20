tell application "System Events"
    set appProcess to first process whose bundle identifier is "cn.mase.morerduo.poc"
    repeat 50 times
        if exists window 1 of appProcess then exit repeat
        delay 0.1
    end repeat

    if not (exists window 1 of appProcess) then error "POC window did not appear"
    tell window 1 of appProcess
        tell group 1
            click (first button whose value of attribute "AXIdentifier" is "loadSampleButton")
            delay 0.2
            click (first button whose value of attribute "AXIdentifier" is "playPauseButton")
            delay 0.2
            if not (exists static text "正在朗读") then error "Playing status was not exposed"
            click (first button whose value of attribute "AXIdentifier" is "playPauseButton")
            delay 0.2
            if not (exists static text "已暂停") then error "Paused status was not exposed"
            click (first button whose value of attribute "AXIdentifier" is "stopButton")
            delay 0.2
            if not (exists static text "文件已就绪") then error "Ready status was not restored"
        end tell
    end tell
end tell

return "PASS Accessibility UI flow"
