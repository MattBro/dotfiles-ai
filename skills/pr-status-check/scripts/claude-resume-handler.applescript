-- ClaudeResume.app — document handler for *.clauderesume files.
-- A .clauderesume file is two lines: line 1 = working dir, line 2 = session id.
-- On open, spawn a new Ghostty tab in that dir running `claude --resume <id>`.

on open theFiles
	repeat with f in theFiles
		set p to POSIX path of f
		set txt to (do shell script "/bin/cat " & quoted form of p)
		set theDir to paragraph 1 of txt
		set theSession to paragraph 2 of txt
		my resumeIn(theDir, theSession)
	end repeat
end open

-- Allow launching with a dir/session pair via `osascript` too (for testing).
on run argv
	if (count of argv) is 2 then
		my resumeIn(item 1 of argv, item 2 of argv)
	end if
end run

on resumeIn(theDir, theSession)
	-- Long timeout so a slow first-run Automation grant (user walks away while
	-- the "Allow control" prompt is up) doesn't abort with AppleEvent timeout (-1712).
	with timeout of 600 seconds
		tell application "Ghostty"
			activate
			set cfg to new surface configuration
			set initial working directory of cfg to theDir
			set initial input of cfg to "claude --resume " & theSession & return
			if (count of windows) is 0 then
				new window with configuration cfg
			else
				new tab in (front window) with configuration cfg
			end if
		end tell
	end timeout
end resumeIn
