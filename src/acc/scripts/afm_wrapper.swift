#!/usr/bin/env swift

import Foundation
import FoundationModels

@available(macOS 26.0, *)
func generate(prompt: String) async {
    do {
        // Initialize the model configuration
        let config = LanguageModelConfiguration()
        
        // Create a session
        let session = try await LanguageModelSession(configuration: config)
        
        // Generate text
        let stream = try await session.generate(prompt)
        
        for try await chunk in stream {
            print(chunk, terminator: "")
        }
        print("") // Ensure newline at end
    } catch {
        print("Error: \(error)")
        exit(1)
    }
}

// Main entry point
if #available(macOS 26.0, *) {
    let args = CommandLine.arguments
    if args.count > 1 && args[1] == "--check" {
        // Just checking if we can import and run.
        exit(0)
    }

    guard args.count > 1 else {
        print("Usage: afm-wrapper <prompt>")
        exit(1)
    }
    
    let prompt = args[1]
    
    // Run async function
    let semaphore = DispatchSemaphore(value: 0)
    Task {
        await generate(prompt: prompt)
        semaphore.signal()
    }
    semaphore.wait()
} else {
    print("Error: FoundationModels requires macOS 26.0 or later.")
    exit(1)
}
